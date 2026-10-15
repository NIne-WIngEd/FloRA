"""Bounded binding to RocksDB 11.8.1's official TransactionDB C API.

Only the authority layer should import this module. It supplies storage, not
semantic validation. A scan/snapshot is NOT a protected predicate: the caller
must track an owner/predicate generation using Transaction.get before publishing.
No raw base-DB write API, alternate engine, or asynchronous durability mode is
exposed. Native transaction handles are short-lived and thread-confined.
"""
import os
from pathlib import Path
import threading

from cffi import FFI


_DECLARATIONS = """
typedef struct rocksdb_options_t rocksdb_options_t;
typedef struct rocksdb_readoptions_t rocksdb_readoptions_t;
typedef struct rocksdb_writeoptions_t rocksdb_writeoptions_t;
typedef struct rocksdb_transactiondb_options_t rocksdb_transactiondb_options_t;
typedef struct rocksdb_transaction_options_t rocksdb_transaction_options_t;
typedef struct rocksdb_transactiondb_t rocksdb_transactiondb_t;
typedef struct rocksdb_transaction_t rocksdb_transaction_t;
typedef struct rocksdb_snapshot_t rocksdb_snapshot_t;
typedef struct rocksdb_iterator_t rocksdb_iterator_t;
typedef struct rocksdb_checkpoint_t rocksdb_checkpoint_t;
rocksdb_options_t* rocksdb_options_create(void);
void rocksdb_options_destroy(rocksdb_options_t*);
void rocksdb_options_set_create_if_missing(rocksdb_options_t*, unsigned char);
rocksdb_readoptions_t* rocksdb_readoptions_create(void);
void rocksdb_readoptions_destroy(rocksdb_readoptions_t*);
void rocksdb_readoptions_set_snapshot(rocksdb_readoptions_t*, const rocksdb_snapshot_t*);
rocksdb_writeoptions_t* rocksdb_writeoptions_create(void);
void rocksdb_writeoptions_destroy(rocksdb_writeoptions_t*);
void rocksdb_writeoptions_set_sync(rocksdb_writeoptions_t*, unsigned char);
void rocksdb_writeoptions_disable_WAL(rocksdb_writeoptions_t*, int);
rocksdb_transactiondb_options_t* rocksdb_transactiondb_options_create(void);
void rocksdb_transactiondb_options_destroy(rocksdb_transactiondb_options_t*);
rocksdb_transaction_options_t* rocksdb_transaction_options_create(void);
void rocksdb_transaction_options_destroy(rocksdb_transaction_options_t*);
void rocksdb_transaction_options_set_set_snapshot(rocksdb_transaction_options_t*, unsigned char);
void rocksdb_transaction_options_set_lock_timeout(rocksdb_transaction_options_t*, int64_t);
rocksdb_transactiondb_t* rocksdb_transactiondb_open(const rocksdb_options_t*,
    const rocksdb_transactiondb_options_t*, const char*, char**);
void rocksdb_transactiondb_close(rocksdb_transactiondb_t*);
rocksdb_transaction_t* rocksdb_transaction_begin(rocksdb_transactiondb_t*,
    const rocksdb_writeoptions_t*, const rocksdb_transaction_options_t*, rocksdb_transaction_t*);
const rocksdb_snapshot_t* rocksdb_transaction_get_snapshot(rocksdb_transaction_t*);
char* rocksdb_transaction_get(rocksdb_transaction_t*, const rocksdb_readoptions_t*,
    const char*, size_t, size_t*, char**);
char* rocksdb_transaction_get_for_update(rocksdb_transaction_t*, const rocksdb_readoptions_t*,
    const char*, size_t, size_t*, unsigned char, char**);
void rocksdb_transaction_put(rocksdb_transaction_t*, const char*, size_t, const char*, size_t, char**);
void rocksdb_transaction_delete(rocksdb_transaction_t*, const char*, size_t, char**);
void rocksdb_transaction_commit(rocksdb_transaction_t*, char**);
void rocksdb_transaction_rollback(rocksdb_transaction_t*, char**);
void rocksdb_transaction_destroy(rocksdb_transaction_t*);
const rocksdb_snapshot_t* rocksdb_transactiondb_create_snapshot(rocksdb_transactiondb_t*);
void rocksdb_transactiondb_release_snapshot(rocksdb_transactiondb_t*, const rocksdb_snapshot_t*);
char* rocksdb_transactiondb_get(rocksdb_transactiondb_t*, const rocksdb_readoptions_t*,
    const char*, size_t, size_t*, char**);
rocksdb_iterator_t* rocksdb_transaction_create_iterator(rocksdb_transaction_t*, const rocksdb_readoptions_t*);
rocksdb_iterator_t* rocksdb_transactiondb_create_iterator(rocksdb_transactiondb_t*, const rocksdb_readoptions_t*);
void rocksdb_iter_destroy(rocksdb_iterator_t*);
unsigned char rocksdb_iter_valid(const rocksdb_iterator_t*);
void rocksdb_iter_seek(rocksdb_iterator_t*, const char*, size_t);
void rocksdb_iter_next(rocksdb_iterator_t*);
const char* rocksdb_iter_key(const rocksdb_iterator_t*, size_t*);
const char* rocksdb_iter_value(const rocksdb_iterator_t*, size_t*);
void rocksdb_iter_get_error(const rocksdb_iterator_t*, char**);
rocksdb_checkpoint_t* rocksdb_transactiondb_checkpoint_object_create(rocksdb_transactiondb_t*, char**);
void rocksdb_checkpoint_create(rocksdb_checkpoint_t*, const char*, uint64_t, char**);
void rocksdb_checkpoint_object_destroy(rocksdb_checkpoint_t*);
void rocksdb_free(void*);
"""


def _bytes(value):
    if not isinstance(value, bytes):
        raise TypeError("native keys and values must be bytes")
    return value


class RocksDB:
    def __init__(self, path, *, lock_timeout_ms=1000):
        # Bound configuration before native allocations. Upstream converts ms to
        # signed microseconds and adds clock time for deadlines. A signed 32-bit
        # ms range leaves ample headroom; this is not a model/run time budget.
        if type(lock_timeout_ms) is not int or not 0 <= lock_timeout_ms <= (1 << 31) - 1:
            raise ValueError("lock_timeout_ms must be an integer in [0, 2147483647]")
        library = os.environ.get("FLORA_ROCKSDB_LIBRARY")
        if not library:
            raise RuntimeError("FLORA_ROCKSDB_LIBRARY must name the pinned native library")
        self.ffi = FFI()
        self.ffi.cdef(_DECLARATIONS)
        self.lib = self.ffi.dlopen(library)
        self._lock = threading.RLock()
        self._children = 0
        self._ptr = self.ffi.NULL
        self._lock_timeout = lock_timeout_ms
        path = Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = os.fsencode(path)
        if b"\0" in encoded:
            raise ValueError("database path contains a null byte")
        options = self.lib.rocksdb_options_create()
        transaction_options = self.lib.rocksdb_transactiondb_options_create()
        try:
            self.lib.rocksdb_options_set_create_if_missing(options, 1)
            self._ptr = self._call(self.lib.rocksdb_transactiondb_open,
                                   options, transaction_options, encoded)
            if self._ptr == self.ffi.NULL:
                raise RuntimeError("native database open returned no handle")
        finally:
            self.lib.rocksdb_transactiondb_options_destroy(transaction_options)
            self.lib.rocksdb_options_destroy(options)

    def _call(self, function, *args):
        error = self.ffi.new("char**")
        result = function(*args, error)
        if error[0] != self.ffi.NULL:
            try:
                message = self.ffi.string(error[0]).decode("utf-8", errors="replace")
            finally:
                self.lib.rocksdb_free(error[0])
            raise RuntimeError(message)
        return result

    def _check(self):
        if self._ptr == self.ffi.NULL:
            raise RuntimeError("database is closed")

    def transaction(self):
        with self._lock:
            self._check()
            return Transaction(self)

    def snapshot(self):
        with self._lock:
            self._check()
            return Snapshot(self)

    def checkpoint(self, path):
        encoded = os.fsencode(Path(path).resolve())
        if b"\0" in encoded:
            raise ValueError("checkpoint path contains a null byte")
        with self._lock:
            self._check()
            checkpoint = self._call(self.lib.rocksdb_transactiondb_checkpoint_object_create, self._ptr)
            try:
                self._call(self.lib.rocksdb_checkpoint_create, checkpoint, encoded, 0)
            finally:
                self.lib.rocksdb_checkpoint_object_destroy(checkpoint)

    def close(self):
        with self._lock:
            if self._children:
                raise RuntimeError("cannot close database with active handles")
            if self._ptr != self.ffi.NULL:
                self.lib.rocksdb_transactiondb_close(self._ptr)
                self._ptr = self.ffi.NULL

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, *args):
        self.close()


class _ReadHandle:
    def _init(self, db):
        self.db, self.ffi, self.lib = db, db.ffi, db.lib
        self._thread = threading.get_ident()
        self._closed = False
        self._read = self.lib.rocksdb_readoptions_create()

    def _check(self):
        if self._closed:
            raise RuntimeError("native handle is closed")
        if threading.get_ident() != self._thread:
            raise RuntimeError("native handle belongs to another thread")

    def _value(self, function, *args):
        length = self.ffi.new("size_t*")
        pointer = self.db._call(function, *args, length)
        if pointer == self.ffi.NULL:
            return None
        try:
            return bytes(self.ffi.buffer(pointer, length[0]))
        finally:
            self.lib.rocksdb_free(pointer)

    def scan(self, prefix=b""):
        self._check()
        _bytes(prefix)
        iterator = self._iterator()
        try:
            self.lib.rocksdb_iter_seek(iterator, prefix, len(prefix))
            result = []
            while self.lib.rocksdb_iter_valid(iterator):
                length = self.ffi.new("size_t*")
                key_pointer = self.lib.rocksdb_iter_key(iterator, length)
                key = bytes(self.ffi.buffer(key_pointer, length[0]))
                if not key.startswith(prefix):
                    break
                value_pointer = self.lib.rocksdb_iter_value(iterator, length)
                result.append((key, bytes(self.ffi.buffer(value_pointer, length[0]))))
                self.lib.rocksdb_iter_next(iterator)
            self.db._call(self.lib.rocksdb_iter_get_error, iterator)
            return result
        finally:
            self.lib.rocksdb_iter_destroy(iterator)

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, *args):
        self.close()


class Transaction(_ReadHandle):
    def __init__(self, db):
        self._init(db)
        writes = options = self._ptr = self._snapshot = self.ffi.NULL
        try:
            writes = self.lib.rocksdb_writeoptions_create()
            options = self.lib.rocksdb_transaction_options_create()
            self.lib.rocksdb_writeoptions_set_sync(writes, 1)
            self.lib.rocksdb_writeoptions_disable_WAL(writes, 0)
            self.lib.rocksdb_transaction_options_set_set_snapshot(options, 1)
            self.lib.rocksdb_transaction_options_set_lock_timeout(options, db._lock_timeout)
            self._ptr = self.lib.rocksdb_transaction_begin(db._ptr, writes, options, self.ffi.NULL)
            if self._ptr == self.ffi.NULL:
                raise RuntimeError("native transaction returned no handle")
            self._snapshot = self.lib.rocksdb_transaction_get_snapshot(self._ptr)
            if self._snapshot == self.ffi.NULL:
                raise RuntimeError("native transaction returned no snapshot")
            self.lib.rocksdb_readoptions_set_snapshot(self._read, self._snapshot)
            db._children += 1
        except BaseException:
            self.lib.rocksdb_readoptions_destroy(self._read)
            if self._snapshot != self.ffi.NULL:
                self.lib.rocksdb_free(self.ffi.cast("void*", self._snapshot))
            if self._ptr != self.ffi.NULL:
                self.lib.rocksdb_transaction_destroy(self._ptr)
            self._closed = True
            raise
        finally:
            if options != self.ffi.NULL:
                self.lib.rocksdb_transaction_options_destroy(options)
            if writes != self.ffi.NULL:
                self.lib.rocksdb_writeoptions_destroy(writes)

    def get(self, key, *, tracked=True):
        self._check()
        _bytes(key)
        if not tracked:
            return self._value(self.lib.rocksdb_transaction_get, self._ptr, self._read, key, len(key))
        length = self.ffi.new("size_t*")
        pointer = self.db._call(self.lib.rocksdb_transaction_get_for_update,
                               self._ptr, self._read, key, len(key), length, 1)
        if pointer == self.ffi.NULL:
            return None
        try:
            return bytes(self.ffi.buffer(pointer, length[0]))
        finally:
            self.lib.rocksdb_free(pointer)

    def put(self, key, value):
        self._check()
        _bytes(key), _bytes(value)
        self.db._call(self.lib.rocksdb_transaction_put, self._ptr, key, len(key), value, len(value))

    def delete(self, key):
        self._check()
        _bytes(key)
        self.db._call(self.lib.rocksdb_transaction_delete, self._ptr, key, len(key))

    def _iterator(self):
        return self.lib.rocksdb_transaction_create_iterator(self._ptr, self._read)

    def commit(self):
        self._check()
        try:
            self.db._call(self.lib.rocksdb_transaction_commit, self._ptr)
        finally:
            self.close()

    def close(self):
        if self._closed:
            return
        self._check()
        with self.db._lock:
            self.lib.rocksdb_readoptions_destroy(self._read)
            # This API returns a malloc-owned wrapper; transaction destruction owns
            # the actual C++ snapshot. See pinned db/c.cc:12522.
            self.lib.rocksdb_free(self.ffi.cast("void*", self._snapshot))
            self.lib.rocksdb_transaction_destroy(self._ptr)
            self.db._children -= 1
            self._closed = True


class Snapshot(_ReadHandle):
    def __init__(self, db):
        self._init(db)
        self._snapshot = self.ffi.NULL
        try:
            self._snapshot = self.lib.rocksdb_transactiondb_create_snapshot(db._ptr)
            if self._snapshot == self.ffi.NULL:
                raise RuntimeError("native database returned no snapshot")
            self.lib.rocksdb_readoptions_set_snapshot(self._read, self._snapshot)
            db._children += 1
        except BaseException:
            self.lib.rocksdb_readoptions_destroy(self._read)
            if self._snapshot != self.ffi.NULL:
                self.lib.rocksdb_transactiondb_release_snapshot(db._ptr, self._snapshot)
            self._closed = True
            raise

    def get(self, key):
        self._check()
        _bytes(key)
        return self._value(self.lib.rocksdb_transactiondb_get, self.db._ptr, self._read, key, len(key))

    def _iterator(self):
        return self.lib.rocksdb_transactiondb_create_iterator(self.db._ptr, self._read)

    def close(self):
        if self._closed:
            return
        self._check()
        with self.db._lock:
            self.lib.rocksdb_readoptions_destroy(self._read)
            self.lib.rocksdb_transactiondb_release_snapshot(self.db._ptr, self._snapshot)
            self.db._children -= 1
            self._closed = True

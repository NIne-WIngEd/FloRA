# Local development build of the same native storage library intended for Alice.
# The supplied archive is the pinned upstream commit, not a modified engine.
FROM flora-frame-contracts-arm64:20261002
USER root
RUN apt-get update && apt-get install -y --no-install-recommends g++ cmake make && rm -rf /var/lib/apt/lists/*
COPY rocksdb.tar.gz /tmp/rocksdb.tar.gz
RUN echo '25dee0decb85ea9a3c8a706b8b627fd67f218e35efae59e23997a4234db32198  /tmp/rocksdb.tar.gz' | sha256sum -c - \
    && mkdir /tmp/rocksdb-src \
    && tar -xf /tmp/rocksdb.tar.gz --strip-components=1 -C /tmp/rocksdb-src \
    && cmake -S /tmp/rocksdb-src -B /tmp/rocksdb-build \
       -DCMAKE_BUILD_TYPE=Release -DPORTABLE=ON -DROCKSDB_BUILD_SHARED=ON \
       -DWITH_TESTS=OFF -DWITH_BENCHMARK_TOOLS=OFF -DWITH_CORE_TOOLS=OFF \
       -DWITH_TOOLS=OFF -DWITH_TRACE_TOOLS=OFF -DWITH_GFLAGS=OFF -DWITH_LIBURING=OFF \
    && cmake --build /tmp/rocksdb-build --target rocksdb-shared -j2 \
    && cp -P /tmp/rocksdb-build/librocksdb.so* /usr/local/lib/ \
    && ldconfig \
    && rm -rf /tmp/rocksdb-build /tmp/rocksdb-src /tmp/rocksdb.tar.gz
ENV FLORA_ROCKSDB_LIBRARY=/usr/local/lib/librocksdb.so
WORKDIR /flora

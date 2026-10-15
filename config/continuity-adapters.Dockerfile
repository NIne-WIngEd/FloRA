FROM flora-continuity-native:rocksdb-11.8.1
RUN python -m pip install --no-cache-dir torch==2.10.0 --index-url https://download.pytorch.org/whl/cpu
ENV OMP_NUM_THREADS=1
ENV PYTHONPATH=/flora/src:/mfm/src:/pe/src:/flora/tests/continuity

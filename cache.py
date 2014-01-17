"""
File: cache.py
Author: Meng Zhuo
Email: mengzhuo1203@gmail.com
Github: https://github.com/mengzhuo/
Description: Django LRU style locmem
"""
import time
from django.core.cache.backends.base import BaseCache
from django.utils.synch import RWLock

MAX_KEYS = 1000

class LocLRUCache(BaseCache):

    """
    Django LRU Threading-safe locmem cache
    """
    def __init__(self, _, params):
        BaseCache.__init__(self, params)
        self._params = params
        self._cache = {}  # entry:(val,expire_time)
        try:
            self._max_entries = int(params.get('max_entries'))
        except:
            self._max_entries = MAX_KEYS

        self._call_seq = {}

        self._call_list = []
        self._lock = RWLock()

    def _lru_purge(self):
        if self._cached_num > self._max_entries:
            # always 1 more entry, therefor we just pop one
            key, val = self._call_seq.popitem()
            self.delete(key)

    def add(self, key, val, timeout=3600):
        if not self.has_key(key):
            self.set(key, val, timeout)

    def set(self, key, val, timeout=3600):
        self._lock.writer_enters()
        try:
            self._cache[key] = (val, time.time() + timeout)
            self._cached_num = len(self._cache)
            self._refresh(key)
            self._lock.writer_leaves()
            self._lru_purge()
        except TypeError:
            pass

    def _refresh(self, key):
        try:
            del self._call_seq[key]
        except:
            pass
        try:
            self._call_seq.update({key: None})
        except:
            pass

    def get(self, key, default=None):

        self._lock.reader_enters()
        try:
            val, exp_time = self._cache.get(key, (default, 0))
            self._lock.reader_leaves()
            if exp_time < time.time():
                self.delete(key)
                val = default
            else:  # still valided
                self._refresh(key)
        except:
            pass
        finally:
            return val

    def delete(self, key):

        self._lock.writer_enters()
        try:
            del self._cache[key]
        except KeyError:
            pass

        try:
            del self._call_seq[key]
        except:
            pass
        self._cached_num = len(self._cache)
        self._lock.writer_leaves()

    def has_key(self, key):
        return self._cache.has_key(key)

    def clear(self):
        [self.delete(key) for key, val in self._cache.iteritems()]

    def __str__(self):
        return u"LRU Cache:{0._params} cached={0._cached_num}".format(self)

CacheClass = LocLRUCache

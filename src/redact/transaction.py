from db import WriteType
from db import get_thread_local
from functools import wraps
from redis.exceptions import WatchError

from db import get_redis_conn
from errors import MaxTransactionRetriesError
from errors import UnknownQueuedWriteTypeError


MAX_TRANSACTION_RETRIES = 500


def execute_queued_write(pipe, queued_write):
    if queued_write.type == WriteType.SET:
        pipe.set(*queued_write.args)
    elif queued_write.type == WriteType.SETEX:
        pipe.setex(*queued_write.args)
    elif queued_write.type == WriteType.HSET:
        pipe.hset(*queued_write.args)
    elif queued_write.type == WriteType.HMSET:
        pipe.hmset(*queued_write.args)
    else:
        raise UnknownQueuedWriteTypeError("{} is an unknown queued write type".format(queued_write.type))


def transaction(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with get_redis_conn().pipeline() as pipe:
            get_thread_local().transaction_pipeline = pipe
            get_thread_local().in_transaction = True
            for i in xrange(MAX_TRANSACTION_RETRIES):
                get_thread_local().queued_writes = {}
                try:
                    ret_value = f(*args, **kwargs)
                    pipe.multi()
                    for queued_write in get_thread_local().queued_writes.values():
                        execute_queued_write(pipe, queued_write)
                    pipe.execute()
                    get_thread_local().in_transaction = False
                    return ret_value
                except WatchError:
                    continue
                except Exception:
                    get_thread_local().in_transaction = False
                    raise
            get_thread_local().in_transaction = False
            raise MaxTransactionRetriesError("Maximum retries done on transaction, bailing out.")
    return wrapper
'''
Copyright: Evan Fosmark. - Released under BSD License
http://www.evanfosmark.com/2009/01/cross-platform-file-locking-support-in-python/
'''
import os, sys, time, errno
 
class FileLockException(Exception):
    pass
 
class FileLock(object):
    """ A file locking mechanism that has context-manager support so 
        you can use it in a with statement. This should be relatively cross
        compatible as it doesn't rely on msvcrt or fcntl for the locking.
    """
 
    def __init__(self, file_name, timeout=10, delay=.05):
        """ Prepare the file locker. Specify the file to lock and optionally
            the maximum timeout and the delay between each attempt to lock.
        """
        self.is_locked = False
        #self.lockfile = os.path.join(os.getcwd(), "%s.lock" % file_name)
        self.lockfile = file_name
        self.pid = os.getpid()
        self.file_name = file_name
        self.timeout = timeout
        self.delay = delay 
        if os.path.isfile(self.file_name):
            fd = os.open(self.file_name, os.O_CREAT|os.O_RDWR)
            oldpid = os.read(fd, 65535)
            os.close(fd);
            if sys.platform == "win32":
                print "YouTube filelock. win32 pid check not implemented"
                #maybe http://code.google.com/p/psutil/
            else:
                if oldpid:
                    try:
                        os.kill(int(oldpid), 0)
                    except OSError:
                        print "YouTube filelock OSError unlinking stale pid file"
                        os.unlink(self.file_name)
                else:
                    print "YouTube filelock removing lock file with no PID in it"
                    os.unlink(self.file_name)
        
    def acquire(self):
        """ Acquire the lock, if possible. If the lock is in use, it check again
            every `wait` seconds. It does this until it either gets the lock or
            exceeds `timeout` number of seconds, in which case it throws 
            an exception.
        """
        print "YouTube filelock pre: " + self.file_name
        start_time = time.time()
        while True:
            try:
                self.fd = os.open(self.lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
                os.write(self.fd, "%d" % self.pid)
                break
            except OSError, e:
                #print "YouTube filelock exception : " + repr(e)
                if e.errno != errno.EEXIST:
                    raise 
                if (time.time() - start_time) >= self.timeout:
                    raise FileLockException("Timeout occured.")
                time.sleep(self.delay)
        self.is_locked = True
        #print "YouTube filelock is locked : " + repr(self.is_locked)
  
    def release(self):
        """ Get rid of the lock by deleting the lockfile. 
            When working in a `with` statement, this gets automatically 
            called at the end.
        """
        if self.is_locked:
            os.close(self.fd)
            os.unlink(self.lockfile)
            self.is_locked = False
 
    def clean(self):
        """ Get rid of the lock by deleting the lockfile. 
        """
        os.unlink(self.lockfile)
        self.is_locked = False
 
 
    def __enter__(self):
        """ Activated when used in the with statement. 
            Should automatically acquire a lock to be used in the with block.
        """
        if not self.is_locked:
            self.acquire()
        return self
 
 
    def __exit__(self, type, value, traceback):
        """ Activated at the end of the with statement.
            It automatically releases the lock if it isn't locked.
        """
        if self.is_locked:
            self.release()
 
 
    def __del__(self):
        """ Make sure that the FileLock instance doesn't leave a lockfile
            lying around.
        """
        self.release()

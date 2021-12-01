import time as time
import sys as sys

def Printtimer(n):
    for i in range(n+1):
        sys.stdout.write(f"\rproceeding in {n-i} seconds...")
        sys.stdout.flush()
        time.sleep(1)

def ImportCSV(Array):
    pass

print(sys.path)
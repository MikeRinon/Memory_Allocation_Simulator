# data structures 
class Block:
    def __init__(self, region, size, pid=None, used=0):
        self.region = region   # which original partition this block belongs to
        self.size = size       # block size in KB
        self.pid = pid         # None means this block is a hole
        self.used = used       # KB really needed (for internal fragmentation)

    def __repr__(self):
        if self.pid is None:
            return f"[HOLE {self.size}]"
        return f"[{self.pid} {self.size}]"


def make_memory(holes):
    return [Block(i, size) for i, size in enumerate(holes)]


# strategies: return the index of the chosen hole (or None) 
def first_fit(mem, size):
    for i, b in enumerate(mem):
        if b.pid is None and b.size >= size:
            return i
    return None


def best_fit(mem, size):
    best = None
    for i, b in enumerate(mem):
        if b.pid is None and b.size >= size:
            if best is None or b.size < mem[best].size:
                best = i
    return best


def worst_fit(mem, size):
    worst = None
    for i, b in enumerate(mem):
        if b.pid is None and b.size >= size:
            if worst is None or b.size > mem[worst].size:
                worst = i
    return worst


STRATEGIES = {"First-Fit": first_fit, "Best-Fit": best_fit, "Worst-Fit": worst_fit}


# operations 
def allocate(mem, pid, size, strategy, split=True):
    """Allocate a process. split=False means fixed partitions (no splitting),
    so the whole hole is given away and the extra space is internal fragmentation."""
    i = strategy(mem, size)
    if i is None:
        return False
    hole = mem[i]
    if split and hole.size > size:
        leftover = Block(hole.region, hole.size - size)
        mem[i] = Block(hole.region, size, pid, size)
        mem.insert(i + 1, leftover)
    else:
        hole.pid = pid
        hole.used = size
    return True


def deallocate(mem, pid):
    for i, b in enumerate(mem):
        if b.pid == pid:
            b.pid = None
            b.used = 0
            break
    else:
        return False
    # merge with next hole in the same region
    j = 0
    while j < len(mem) - 1:
        a, c = mem[j], mem[j + 1]
        if a.pid is None and c.pid is None and a.region == c.region:
            a.size += c.size
            mem.pop(j + 1)
        else:
            j += 1
    return True


# metrics 
def holes_of(mem):
    return [b.size for b in mem if b.pid is None]


def external_frag(mem):
    h = holes_of(mem)
    total = sum(h)
    largest = max(h) if h else 0
    return total, largest, total - largest


def internal_frag(mem):
    return sum(b.size - b.used for b in mem if b.pid is not None)


# run one scenario 
def run(holes, events, strategy_name, split=True, verbose=True):
    strategy = STRATEGIES[strategy_name]
    mem = make_memory(holes)
    allocated, rejected = [], []
    log = []
    for ev in events:
        if ev[0] == "alloc":
            _, pid, size = ev
            ok = allocate(mem, pid, size, strategy, split)
            (allocated if ok else rejected).append(pid)
            log.append(f"  alloc {pid}={size}: {'OK' if ok else 'REJECTED'}   map={mem}")
        else:
            _, pid = ev
            deallocate(mem, pid)
            log.append(f"  free  {pid}:        map={mem}")
    total, largest, ext = external_frag(mem)
    result = dict(allocated=allocated, rejected=rejected, mem=mem,
                  total_free=total, largest=largest, external=ext,
                  internal=internal_frag(mem), log=log)
    if verbose:
        print(f"\n=== {strategy_name} ({'variable' if split else 'fixed'} partitions) ===")
        for line in log:
            print(line)
        print(f"  Allocated: {allocated}")
        print(f"  Rejected : {rejected}")
        print(f"  Final map: {mem}")
        print(f"  Total free = {total} KB, largest hole = {largest} KB, "
              f"external fragmentation (free - largest) = {ext} KB")
        print(f"  Internal fragmentation = {result['internal']} KB")
    return result


def main():
    # Part 1.2 test data 
    holes = [100, 500, 200, 300, 600]
    events = [("alloc", "P1", 212), ("alloc", "P2", 417), ("alloc", "P3", 112),
              ("alloc", "P4", 426), ("free", "P2"), ("alloc", "P5", 200)]
    print("##### TEST 1: variable partitions (holes are split) #####")
    print("Initial holes:", holes)
    for name in STRATEGIES:
        run(holes, events, name, split=True)

    print("\n\n##### TEST 2: fixed partitions (no splitting) #####")
    for name in STRATEGIES:
        run(holes, events, name, split=False)

    # Part 1.3: scenario where Best-Fit is worse than First-Fit 
    holes2 = [300, 200]
    events2 = [("alloc", "A", 100), ("alloc", "B", 150), ("alloc", "C", 200)]
    print("\n\n##### TEST 3: custom scenario (Best-Fit worse than First-Fit) #####")
    print("Initial holes:", holes2)
    for name in ["First-Fit", "Best-Fit"]:
        run(holes2, events2, name, split=True)


if __name__ == "__main__":
    main()
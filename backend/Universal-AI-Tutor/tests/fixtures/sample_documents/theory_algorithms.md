# Algorithm Analysis and Data Structures

## Big O Notation

### Time Complexity

Big O notation describes the upper bound of an algorithm's growth rate. It answers: "How does the runtime grow as input size increases?"

Common time complexities (from fastest to slowest):

1. **O(1) - Constant Time**
   - Runtime doesn't depend on input size
   - Examples: Array access, hash table lookup (average case)
   
2. **O(log n) - Logarithmic Time**
   - Runtime grows logarithmically
   - Examples: Binary search, balanced tree operations
   
3. **O(n) - Linear Time**
   - Runtime grows linearly with input
   - Examples: Linear search, iterating through array
   
4. **O(n log n) - Linearithmic Time**
   - Efficient sorting algorithms
   - Examples: Merge sort, heap sort, quick sort (average case)
   
5. **O(n²) - Quadratic Time**
   - Nested loops over input
   - Examples: Bubble sort, selection sort, simple matrix multiplication
   
6. **O(2ⁿ) - Exponential Time**
   - Runtime doubles with each addition to input
   - Examples: Recursive Fibonacci, brute-force subsets
   
7. **O(n!) - Factorial Time**
   - Extremely slow growth
   - Examples: Generating all permutations, traveling salesman (brute force)

### Space Complexity

Describes memory usage relative to input size. Uses same notation as time complexity.

## Sorting Algorithms

### Bubble Sort
- **Time Complexity**: O(n²) average and worst case, O(n) best case
- **Space Complexity**: O(1)
- **Stable**: Yes
- Repeatedly swaps adjacent elements if they're in wrong order

### Selection Sort
- **Time Complexity**: O(n²) all cases
- **Space Complexity**: O(1)
- **Stable**: No
- Finds minimum element and moves it to sorted portion

### Insertion Sort
- **Time Complexity**: O(n²) average and worst, O(n) best
- **Space Complexity**: O(1)
- **Stable**: Yes
- Builds sorted array one element at a time
- Efficient for small or nearly-sorted data

### Merge Sort
- **Time Complexity**: O(n log n) all cases
- **Space Complexity**: O(n)
- **Stable**: Yes
- Divide-and-conquer: splits array, recursively sorts, merges

### Quick Sort
- **Time Complexity**: O(n log n) average, O(n²) worst
- **Space Complexity**: O(log n)
- **Stable**: No (typically)
- Divide-and-conquer: picks pivot, partitions around it

### Heap Sort
- **Time Complexity**: O(n log n) all cases
- **Space Complexity**: O(1)
- **Stable**: No
- Uses heap data structure

## Searching Algorithms

### Linear Search
- **Time Complexity**: O(n)
- **Space Complexity**: O(1)
- Checks every element sequentially
- Works on unsorted data

### Binary Search
- **Time Complexity**: O(log n)
- **Space Complexity**: O(1) iterative, O(log n) recursive
- Requires sorted array
- Repeatedly divides search space in half

Algorithm:
1. Compare target with middle element
2. If equal, found
3. If target smaller, search left half
4. If target larger, search right half
5. Repeat until found or search space empty

## Data Structures

### Arrays
- **Access**: O(1)
- **Search**: O(n)
- **Insertion**: O(n) (requires shifting)
- **Deletion**: O(n)
- Contiguous memory, fixed or dynamic size

### Linked Lists
- **Access**: O(n)
- **Search**: O(n)
- **Insertion**: O(1) (with pointer to position)
- **Deletion**: O(1) (with pointer to position)
- Non-contiguous memory, dynamic size

Types:
- Singly linked: Each node points to next
- Doubly linked: Each node points to next and previous
- Circular: Last node points to first

### Stacks
- **Push**: O(1)
- **Pop**: O(1)
- **Peek**: O(1)
- LIFO (Last In, First Out)
- Applications: Function call stack, undo/redo, expression evaluation

### Queues
- **Enqueue**: O(1)
- **Dequeue**: O(1)
- **Peek**: O(1)
- FIFO (First In, First Out)
- Applications: Task scheduling, breadth-first search

### Hash Tables
- **Insert**: O(1) average
- **Delete**: O(1) average
- **Search**: O(1) average
- Uses hash function to map keys to buckets
- Collision handling: Chaining or open addressing

### Trees

**Binary Tree**: Each node has at most two children

**Binary Search Tree (BST)**:
- Left subtree contains smaller values
- Right subtree contains larger values
- **Search/Insert/Delete**: O(log n) average, O(n) worst

**Balanced Trees**:
- AVL Tree: Maintains height balance
- Red-Black Tree: Maintains color property
- **All operations**: O(log n) guaranteed

**Heap**:
- Complete binary tree
- Max-heap: Parent ≥ children
- Min-heap: Parent ≤ children
- **Insert/Delete**: O(log n)
- **Find min/max**: O(1)

### Graphs

Representations:
- **Adjacency Matrix**: O(V²) space, O(1) edge lookup
- **Adjacency List**: O(V + E) space, O(degree) edge lookup

Traversal Algorithms:
- **Depth-First Search (DFS)**: Uses stack, explores deep before wide
- **Breadth-First Search (BFS)**: Uses queue, explores level by level

## Algorithm Design Paradigms

### Divide and Conquer
Break problem into smaller subproblems, solve recursively, combine results.
Examples: Merge sort, quick sort, binary search

### Dynamic Programming
Break problem into overlapping subproblems, store results to avoid recomputation.
Requirements:
1. Optimal substructure
2. Overlapping subproblems

Examples: Fibonacci, longest common subsequence, knapsack problem

### Greedy Algorithms
Make locally optimal choice at each step, hoping for global optimum.
Works when:
1. Greedy choice property
2. Optimal substructure

Examples: Dijkstra's shortest path, Huffman coding, activity selection

### Backtracking
Build solution incrementally, abandoning candidates that fail constraints.
Examples: N-queens, Sudoku solver, maze solving

## Graph Algorithms

### Shortest Path

**Dijkstra's Algorithm**:
- Single-source shortest path
- Non-negative edge weights
- Time: O((V + E) log V) with priority queue

**Bellman-Ford Algorithm**:
- Single-source shortest path
- Handles negative weights
- Detects negative cycles
- Time: O(VE)

**Floyd-Warshall Algorithm**:
- All-pairs shortest path
- Time: O(V³)

### Minimum Spanning Tree

**Kruskal's Algorithm**:
- Sort edges by weight
- Add edges that don't create cycle
- Time: O(E log E)

**Prim's Algorithm**:
- Start from vertex, grow tree
- Add minimum weight edge to tree
- Time: O(E log V) with priority queue

### Topological Sort
- Orders vertices in directed acyclic graph (DAG)
- Every edge goes from earlier to later vertex
- Applications: Task scheduling, dependency resolution
- Time: O(V + E)

## Complexity Classes

### P (Polynomial Time)
Problems solvable in polynomial time by deterministic Turing machine.
Examples: Sorting, searching, shortest path

### NP (Nondeterministic Polynomial Time)
Problems verifiable in polynomial time.
If solution given, can verify it quickly.
Examples: Subset sum, graph coloring, SAT

### NP-Complete
Hardest problems in NP. If any NP-complete problem has polynomial solution, then P = NP.
Examples: Traveling salesman, Hamiltonian cycle, SAT

### NP-Hard
At least as hard as NP-complete problems, but not necessarily in NP.
Examples: Halting problem, optimization versions of NP-complete problems

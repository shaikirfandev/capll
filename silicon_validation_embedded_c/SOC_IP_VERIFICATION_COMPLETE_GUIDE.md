# SoC/IP Verification Complete Learning Guide
## SystemVerilog, UVM, and Advanced Verification Methodologies

**Target Role:** Digital Verification Engineer (SoC/IP/Subsystem Verification)  
**Technologies:** SystemVerilog, UVM, Assertions, Coverage, Formal Verification  
**Date:** May 2026  
**Experience Level:** Junior to Senior Verification Engineer

---

## Table of Contents

1. [Verification Fundamentals](#1-verification-fundamentals)
2. [SystemVerilog for Verification](#2-systemverilog-for-verification)
3. [UVM Methodology](#3-uvm-methodology)
4. [Testbench Architecture](#4-testbench-architecture)
5. [Test Case Development](#5-test-case-development)
6. [Sequences and Virtual Sequences](#6-sequences-and-virtual-sequences)
7. [Assertions and Checkers](#7-assertions-and-checkers)
8. [Coverage Models](#8-coverage-models)
9. [Functional Verification](#9-functional-verification)
10. [Regression and Random Verification](#10-regression-and-random-verification)
11. [Debug Techniques](#11-debug-techniques)
12. [Code and Functional Coverage Analysis](#12-code-and-functional-coverage-analysis)
13. [SoC Integration Verification](#13-soc-integration-verification)
14. [Verification Closure](#14-verification-closure)
15. [Tools and Environment Setup](#15-tools-and-environment-setup)
16. [Industry Best Practices](#16-industry-best-practices)
17. [Interview Preparation](#17-interview-preparation)
18. [Hands-On Projects](#18-hands-on-projects)

---

## 1. Verification Fundamentals

### 1.1 Verification vs Validation

**Verification:**
- "Are we building the product right?"
- Checking design against specifications
- Simulation-based, formal verification, emulation
- Done throughout design cycle

**Validation:**
- "Are we building the right product?"
- Checking if product meets customer needs
- Post-silicon, real hardware testing
- Done after tapeout

### 1.2 Verification Plan Components

```
Verification Plan Structure:
├── Design Specifications Review
├── Feature List Extraction
├── Verification Strategy
│   ├── Block-level verification
│   ├── Subsystem verification
│   └── SoC-level verification
├── Coverage Goals
│   ├── Code coverage (Line, Branch, FSM, Expression)
│   ├── Functional coverage (Features, corner cases)
│   └── Assertion coverage
├── Test Plan
│   ├── Directed tests
│   ├── Constrained random tests
│   └── Regression suite
├── Resource Planning
│   ├── Testbench architecture
│   ├── Reusable components (VIPs)
│   └── Tools and compute resources
└── Schedule and Milestones
```

### 1.3 Verification Stages

```
Stage 1: Planning
- Specification review
- Verification plan creation
- Testbench architecture design

Stage 2: Environment Development
- UVM testbench development
- VIP integration
- Assertion development

Stage 3: Test Development
- Directed tests
- Constrained random tests
- Coverage model creation

Stage 4: Execution
- Functional verification
- Regression testing
- Coverage closure

Stage 5: Debug and Analysis
- Bug triage
- Coverage analysis
- Design fixes verification

Stage 6: Closure
- Coverage metrics met (>95% code, >90% functional)
- All bugs closed or waived
- Sign-off documentation
```

### 1.4 Verification Metrics

```systemverilog
// Key Verification Metrics

1. Code Coverage Metrics:
   - Line Coverage: % of lines executed
   - Branch Coverage: % of branches taken
   - FSM Coverage: % of FSM states/transitions
   - Expression Coverage: % of boolean expressions
   - Toggle Coverage: % of signals toggled

2. Functional Coverage Metrics:
   - Feature Coverage: % of features verified
   - Corner Case Coverage: % of boundary conditions
   - Cross Coverage: % of feature combinations

3. Bug Metrics:
   - Bugs found per week
   - Bug severity distribution
   - Bug closure rate
   - Escaped bugs (found in validation/silicon)

4. Verification Progress:
   - Tests passing/total tests
   - Coverage trends (weekly/monthly)
   - Verification cycles consumed
```

---

## 2. SystemVerilog for Verification

### 2.1 Data Types and Variables

```systemverilog
// Basic Data Types
module sv_basics;
  
  // 2-state types (0, 1)
  bit        single_bit;          // 1-bit
  bit [7:0]  byte_data;            // 8-bit vector
  int        signed_int;           // 32-bit signed
  longint    long_data;            // 64-bit signed
  
  // 4-state types (0, 1, X, Z)
  logic        single_logic;       // 1-bit with X/Z
  logic [31:0] word;               // 32-bit word
  reg [7:0]    legacy_reg;         // Compatible with Verilog
  wire [3:0]   bus;                // Wire type
  
  // Real types
  real         float_val;          // Double precision
  shortreal    half_float;         // Single precision
  
  // String type
  string       message = "Hello Verification";
  
  // Enumerated types
  typedef enum {IDLE, READ, WRITE, WAIT} state_t;
  state_t current_state;
  
  // Structures
  typedef struct packed {
    logic [7:0]  opcode;
    logic [15:0] addr;
    logic [31:0] data;
    logic        valid;
  } packet_t;
  
  packet_t tx_packet;
  
  // Unions
  typedef union packed {
    logic [31:0] word;
    logic [7:0]  bytes[4];
  } word_union_t;
  
  // Dynamic arrays
  int dynamic_array[];
  
  // Queues
  int queue[$];
  
  // Associative arrays
  int assoc_array[string];
  
  initial begin
    // Dynamic array operations
    dynamic_array = new[10];
    dynamic_array[0] = 100;
    
    // Queue operations
    queue.push_back(5);
    queue.push_front(3);
    int val = queue.pop_back();
    
    // Associative array
    assoc_array["key1"] = 42;
    assoc_array["key2"] = 99;
    
    if (assoc_array.exists("key1"))
      $display("Found key1 = %0d", assoc_array["key1"]);
    
    // Structure usage
    tx_packet.opcode = 8'hA5;
    tx_packet.addr   = 16'h1234;
    tx_packet.data   = 32'hDEAD_BEEF;
    tx_packet.valid  = 1'b1;
    
    $display("Packet: opcode=%h, addr=%h, data=%h", 
             tx_packet.opcode, tx_packet.addr, tx_packet.data);
  end
  
endmodule
```

### 2.2 Procedural Blocks and Timing Control

```systemverilog
module timing_control;
  
  logic clk;
  logic [7:0] data;
  logic valid, ready;
  
  // Clock generation
  initial begin
    clk = 0;
    forever #5 clk = ~clk; // 10ns period, 100MHz
  end
  
  // always_ff - Sequential logic (flip-flops)
  always_ff @(posedge clk) begin
    if (valid && ready)
      data <= data + 1;
  end
  
  // always_comb - Combinational logic
  logic [7:0] result;
  always_comb begin
    result = data * 2;
  end
  
  // always_latch - Latch inference (avoid in RTL)
  logic latch_out;
  always_latch begin
    if (valid)
      latch_out = data[0];
  end
  
  // Timing controls
  initial begin
    // Delay control
    #10ns;                    // Wait 10ns
    
    // Event control
    @(posedge clk);           // Wait for posedge of clk
    @(negedge clk);           // Wait for negedge of clk
    @(valid);                 // Wait for any change on valid
    
    // Level-sensitive event
    wait(ready == 1'b1);      // Wait until ready is high
    
    // Intra-assignment delay
    data = #5 8'hAA;          // Assign after 5ns
    
    // Repeat
    repeat(10) @(posedge clk); // Wait 10 clock cycles
    
    // Fork-join for parallel execution
    fork
      begin
        #10 $display("Process 1 at %0t", $time);
      end
      begin
        #20 $display("Process 2 at %0t", $time);
      end
    join
    
    // Fork-join_any - proceeds when first thread completes
    fork
      #50 $display("Long task");
      #10 $display("Short task");
    join_any
    $display("Continued after first completion");
    
    // Fork-join_none - doesn't wait
    fork
      #10 $display("Background task");
    join_none
    $display("Continues immediately");
    
    #100 $finish;
  end
  
endmodule
```

### 2.3 Constraint Random Verification

```systemverilog
// Transaction class with constraints
class packet_transaction;
  
  // Randomizable variables
  rand bit [7:0]  opcode;
  rand bit [15:0] addr;
  rand bit [31:0] data;
  rand int        length;
  randc bit [3:0] burst_type; // randc = random-cyclic
  
  // Non-random control variables
  bit [31:0] timestamp;
  int packet_id;
  
  // Constraints
  constraint valid_opcode {
    opcode inside {8'h01, 8'h02, 8'h03, 8'h04}; // Only valid opcodes
  }
  
  constraint addr_range {
    addr >= 16'h1000;
    addr <= 16'hFFFF;
    addr[1:0] == 2'b00; // Word-aligned addresses
  }
  
  constraint length_constraint {
    length inside {[1:256]};
    length % 4 == 0; // Multiple of 4
  }
  
  // Conditional constraints
  constraint burst_constraint {
    if (opcode == 8'h03) // BURST_WRITE
      length inside {[4:64]};
    else
      length inside {[1:16]};
  }
  
  // Distribution constraint
  constraint data_distribution {
    data dist {
      32'h0000_0000 := 10,        // Weight 10
      [32'h0001:32'h00FF] := 40,  // Weight 40
      [32'h0100:32'hFFFF] := 50   // Weight 50
    };
  }
  
  // Implication constraint
  constraint addr_data_implication {
    (addr < 16'h2000) -> (data[31:16] == 16'h0);
  }
  
  // Solve-before constraint
  constraint solve_order {
    solve opcode before length;
  }
  
  // Functions
  function void post_randomize();
    timestamp = $time;
    $display("Packet randomized at time %0t", timestamp);
    $display("  opcode=0x%h, addr=0x%h, data=0x%h, length=%0d",
             opcode, addr, data, length);
  endfunction
  
  function void pre_randomize();
    static int id_counter = 0;
    packet_id = id_counter++;
  endfunction
  
  // Copy function
  function packet_transaction copy();
    packet_transaction pkt = new();
    pkt.opcode = this.opcode;
    pkt.addr   = this.addr;
    pkt.data   = this.data;
    pkt.length = this.length;
    return pkt;
  endfunction
  
  // Compare function
  function bit compare(packet_transaction pkt);
    return (this.opcode == pkt.opcode &&
            this.addr   == pkt.addr   &&
            this.data   == pkt.data   &&
            this.length == pkt.length);
  endfunction
  
endclass

// Example usage
module constraint_example;
  
  packet_transaction pkt;
  
  initial begin
    pkt = new();
    
    // Standard randomization
    if (!pkt.randomize()) begin
      $error("Randomization failed");
    end
    
    // Randomization with inline constraints
    if (!pkt.randomize() with {
      opcode == 8'h01;
      addr inside {[16'h1000:16'h2000]};
    }) begin
      $error("Inline randomization failed");
    end
    
    // Disable specific constraints
    pkt.valid_opcode.constraint_mode(0); // Disable
    if (!pkt.randomize()) $error("Failed");
    pkt.valid_opcode.constraint_mode(1); // Re-enable
    
    // Randomize only specific variables
    if (!pkt.randomize(addr, data)) begin
      $error("Partial randomization failed");
    end
    
    // Generate multiple random packets
    repeat(10) begin
      pkt = new();
      assert(pkt.randomize());
      // Use packet...
    end
  end
  
endmodule
```

### 2.4 Object-Oriented Programming

```systemverilog
// Base class
virtual class base_transaction;
  
  rand bit [31:0] addr;
  rand bit [31:0] data;
  
  static int transaction_count = 0;
  int trans_id;
  
  // Constructor
  function new();
    trans_id = transaction_count++;
  endfunction
  
  // Pure virtual function (must be overridden)
  pure virtual function void display();
  
  // Virtual function (can be overridden)
  virtual function void print_header();
    $display("Transaction ID: %0d", trans_id);
  endfunction
  
endclass

// Extended class - Read Transaction
class read_transaction extends base_transaction;
  
  rand bit [3:0] burst_len;
  
  constraint read_constraints {
    burst_len inside {[1:16]};
  }
  
  // Constructor with super call
  function new();
    super.new();
  endfunction
  
  // Implement pure virtual function
  function void display();
    print_header();
    $display("READ: addr=0x%h, burst_len=%0d", addr, burst_len);
  endfunction
  
endclass

// Extended class - Write Transaction
class write_transaction extends base_transaction;
  
  rand bit [31:0] write_data[];
  rand int byte_enable;
  
  constraint write_constraints {
    write_data.size() inside {[1:64]};
    byte_enable inside {[0:15]};
  }
  
  function new();
    super.new();
  endfunction
  
  function void display();
    print_header();
    $display("WRITE: addr=0x%h, data_words=%0d", addr, write_data.size());
    foreach(write_data[i])
      $display("  data[%0d] = 0x%h", i, write_data[i]);
  endfunction
  
endclass

// Parameterized class
class fifo #(parameter int DEPTH = 8, parameter type T = int);
  
  T queue[$];
  
  function void push(T item);
    if (queue.size() < DEPTH)
      queue.push_back(item);
    else
      $error("FIFO overflow");
  endfunction
  
  function T pop();
    if (queue.size() > 0)
      return queue.pop_front();
    else begin
      $error("FIFO underflow");
      return T'(0);
    end
  endfunction
  
  function bit is_full();
    return (queue.size() == DEPTH);
  endfunction
  
  function bit is_empty();
    return (queue.size() == 0);
  endfunction
  
endclass

// Usage example
module oop_example;
  
  read_transaction  rd_trans;
  write_transaction wr_trans;
  base_transaction  trans_handle; // Polymorphic handle
  
  fifo #(.DEPTH(16), .T(int)) int_fifo;
  fifo #(.DEPTH(32), .T(bit[31:0])) word_fifo;
  
  initial begin
    // Create objects
    rd_trans = new();
    wr_trans = new();
    
    // Randomize
    void'(rd_trans.randomize());
    void'(wr_trans.randomize());
    
    // Polymorphism
    trans_handle = rd_trans;
    trans_handle.display(); // Calls read_transaction::display()
    
    trans_handle = wr_trans;
    trans_handle.display(); // Calls write_transaction::display()
    
    // Parameterized class usage
    int_fifo = new();
    int_fifo.push(100);
    int_fifo.push(200);
    $display("Popped: %0d", int_fifo.pop());
    
    word_fifo = new();
    word_fifo.push(32'hDEADBEEF);
    $display("Popped: 0x%h", word_fifo.pop());
  end
  
endmodule
```

### 2.5 Interfaces and Modports

```systemverilog
// AXI4-Lite Interface Definition
interface axi4lite_if #(
  parameter ADDR_WIDTH = 32,
  parameter DATA_WIDTH = 32
) (
  input logic clk,
  input logic resetn
);
  
  // Write Address Channel
  logic [ADDR_WIDTH-1:0] awaddr;
  logic [2:0]            awprot;
  logic                  awvalid;
  logic                  awready;
  
  // Write Data Channel
  logic [DATA_WIDTH-1:0]   wdata;
  logic [DATA_WIDTH/8-1:0] wstrb;
  logic                    wvalid;
  logic                    wready;
  
  // Write Response Channel
  logic [1:0] bresp;
  logic       bvalid;
  logic       bready;
  
  // Read Address Channel
  logic [ADDR_WIDTH-1:0] araddr;
  logic [2:0]            arprot;
  logic                  arvalid;
  logic                  arready;
  
  // Read Data Channel
  logic [DATA_WIDTH-1:0] rdata;
  logic [1:0]            rresp;
  logic                  rvalid;
  logic                  rready;
  
  // Modport for Master (DUT perspective)
  modport master (
    output awaddr, awprot, awvalid,
    input  awready,
    output wdata, wstrb, wvalid,
    input  wready,
    input  bresp, bvalid,
    output bready,
    output araddr, arprot, arvalid,
    input  arready,
    input  rdata, rresp, rvalid,
    output rready
  );
  
  // Modport for Slave (Testbench/Monitor perspective)
  modport slave (
    input  awaddr, awprot, awvalid,
    output awready,
    input  wdata, wstrb, wvalid,
    output wready,
    output bresp, bvalid,
    input  bready,
    input  araddr, arprot, arvalid,
    output arready,
    output rdata, rresp, rvalid,
    input  rready
  );
  
  // Modport for Monitor (passive observation)
  modport monitor (
    input awaddr, awprot, awvalid, awready,
    input wdata, wstrb, wvalid, wready,
    input bresp, bvalid, bready,
    input araddr, arprot, arvalid, arready,
    input rdata, rresp, rvalid, rready,
    input clk, resetn
  );
  
  // Clocking block for synchronous testbench
  clocking cb @(posedge clk);
    default input #1ns output #1ns; // Setup and hold times
    
    output awaddr, awprot, awvalid;
    input  awready;
    output wdata, wstrb, wvalid;
    input  wready;
    input  bresp, bvalid;
    output bready;
    output araddr, arprot, arvalid;
    input  arready;
    input  rdata, rresp, rvalid;
    output rready;
  endclocking
  
  modport tb (clocking cb, input resetn);
  
  // Helper tasks in interface
  task automatic write_single(
    input  logic [ADDR_WIDTH-1:0] addr,
    input  logic [DATA_WIDTH-1:0] data,
    output logic [1:0]            resp
  );
    // Write Address
    @(cb);
    cb.awaddr  <= addr;
    cb.awprot  <= 3'b000;
    cb.awvalid <= 1'b1;
    
    wait(cb.awready);
    @(cb);
    cb.awvalid <= 1'b0;
    
    // Write Data
    cb.wdata  <= data;
    cb.wstrb  <= '1; // All bytes
    cb.wvalid <= 1'b1;
    
    wait(cb.wready);
    @(cb);
    cb.wvalid <= 1'b0;
    
    // Write Response
    cb.bready <= 1'b1;
    wait(cb.bvalid);
    resp = cb.bresp;
    @(cb);
    cb.bready <= 1'b0;
  endtask
  
  task automatic read_single(
    input  logic [ADDR_WIDTH-1:0] addr,
    output logic [DATA_WIDTH-1:0] data,
    output logic [1:0]            resp
  );
    // Read Address
    @(cb);
    cb.araddr  <= addr;
    cb.arprot  <= 3'b000;
    cb.arvalid <= 1'b1;
    
    wait(cb.arready);
    @(cb);
    cb.arvalid <= 1'b0;
    
    // Read Data
    cb.rready <= 1'b1;
    wait(cb.rvalid);
    data = cb.rdata;
    resp = cb.rresp;
    @(cb);
    cb.rready <= 1'b0;
  endtask
  
  // Assertions can be embedded in interface
  property aw_valid_until_ready;
    @(posedge clk) disable iff (!resetn)
    awvalid && !awready |=> awvalid;
  endproperty
  
  assert property (aw_valid_until_ready)
    else $error("AW channel violated handshake protocol");
  
endinterface

// DUT Module using interface
module axi_slave #(
  parameter ADDR_WIDTH = 32,
  parameter DATA_WIDTH = 32
) (
  axi4lite_if.slave axi_if
);
  
  logic [DATA_WIDTH-1:0] memory [logic[ADDR_WIDTH-1:0]];
  
  // Write logic
  always_ff @(posedge axi_if.clk or negedge axi_if.resetn) begin
    if (!axi_if.resetn) begin
      axi_if.awready <= 1'b0;
      axi_if.wready  <= 1'b0;
      axi_if.bvalid  <= 1'b0;
    end else begin
      // Simplified write logic
      if (axi_if.awvalid && axi_if.wvalid) begin
        memory[axi_if.awaddr] <= axi_if.wdata;
        axi_if.bvalid <= 1'b1;
        axi_if.bresp  <= 2'b00; // OKAY
      end
      if (axi_if.bready && axi_if.bvalid)
        axi_if.bvalid <= 1'b0;
    end
  end
  
  // Read logic (simplified)
  always_ff @(posedge axi_if.clk or negedge axi_if.resetn) begin
    if (!axi_if.resetn) begin
      axi_if.arready <= 1'b0;
      axi_if.rvalid  <= 1'b0;
    end else begin
      if (axi_if.arvalid) begin
        axi_if.rdata  <= memory[axi_if.araddr];
        axi_if.rvalid <= 1'b1;
        axi_if.rresp  <= 2'b00; // OKAY
      end
      if (axi_if.rready && axi_if.rvalid)
        axi_if.rvalid <= 1'b0;
    end
  end
  
endmodule

// Testbench using interface
module interface_tb;
  
  logic clk, resetn;
  
  // Instantiate interface
  axi4lite_if #(
    .ADDR_WIDTH(32),
    .DATA_WIDTH(32)
  ) axi_if (
    .clk(clk),
    .resetn(resetn)
  );
  
  // Instantiate DUT
  axi_slave #(
    .ADDR_WIDTH(32),
    .DATA_WIDTH(32)
  ) dut (
    .axi_if(axi_if.slave)
  );
  
  // Clock generation
  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end
  
  // Test stimulus
  initial begin
    logic [31:0] read_data;
    logic [1:0]  resp;
    
    resetn = 0;
    #20 resetn = 1;
    
    // Use interface tasks
    axi_if.write_single(32'h1000, 32'hDEADBEEF, resp);
    $display("Write response: %0d", resp);
    
    axi_if.read_single(32'h1000, read_data, resp);
    $display("Read data: 0x%h, response: %0d", read_data, resp);
    
    #100 $finish;
  end
  
endmodule
```

---

## 3. UVM Methodology

### 3.1 UVM Architecture Overview

```
UVM Testbench Hierarchy:

uvm_test (test)
    └── uvm_env (environment)
            ├── uvm_agent (master_agent)
            │       ├── uvm_sequencer (sequencer)
            │       ├── uvm_driver (driver)
            │       └── uvm_monitor (monitor)
            ├── uvm_agent (slave_agent)
            │       ├── uvm_sequencer (sequencer)
            │       ├── uvm_driver (driver)
            │       └── uvm_monitor (monitor)
            ├── uvm_scoreboard (scoreboard)
            ├── uvm_subscriber (coverage_collector)
            └── virtual_sequencer (v_sequencer)

Phases:
build → connect → end_of_elaboration → start_of_simulation →
run (reset→configure→main→shutdown) → extract → check → report → final
```

### 3.2 UVM Transaction

```systemverilog
// Base transaction class
class axi_transaction extends uvm_sequence_item;
  
  // Transaction fields
  rand bit [31:0]      addr;
  rand bit [31:0]      data;
  rand bit [3:0]       strb;
  rand axi_access_type access_type; // READ or WRITE
  rand int             delay;
  
  // Response fields
  bit [31:0] read_data;
  bit [1:0]  resp;
  
  // Enum for access type
  typedef enum {READ, WRITE} axi_access_type;
  
  // Constraints
  constraint valid_addr {
    addr[1:0] == 2'b00; // Word aligned
    addr inside {[32'h0000_0000:32'h0FFF_FFFF]};
  }
  
  constraint reasonable_delay {
    delay inside {[0:10]};
  }
  
  // UVM macros for automation
  `uvm_object_utils_begin(axi_transaction)
    `uvm_field_int(addr, UVM_ALL_ON)
    `uvm_field_int(data, UVM_ALL_ON)
    `uvm_field_int(strb, UVM_ALL_ON)
    `uvm_field_enum(axi_access_type, access_type, UVM_ALL_ON)
    `uvm_field_int(delay, UVM_ALL_ON)
    `uvm_field_int(read_data, UVM_ALL_ON)
    `uvm_field_int(resp, UVM_ALL_ON)
  `uvm_object_utils_end
  
  // Constructor
  function new(string name = "axi_transaction");
    super.new(name);
  endfunction
  
  // Custom do_copy
  virtual function void do_copy(uvm_object rhs);
    axi_transaction rhs_;
    if (!$cast(rhs_, rhs)) begin
      `uvm_fatal(get_type_name(), "Cast failed in do_copy")
    end
    super.do_copy(rhs);
    this.addr        = rhs_.addr;
    this.data        = rhs_.data;
    this.strb        = rhs_.strb;
    this.access_type = rhs_.access_type;
    this.delay       = rhs_.delay;
    this.read_data   = rhs_.read_data;
    this.resp        = rhs_.resp;
  endfunction
  
  // Custom do_compare
  virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
    axi_transaction rhs_;
    bit result;
    if (!$cast(rhs_, rhs)) begin
      `uvm_fatal(get_type_name(), "Cast failed in do_compare")
      return 0;
    end
    result = super.do_compare(rhs, comparer);
    result &= (this.addr == rhs_.addr);
    result &= (this.data == rhs_.data);
    result &= (this.access_type == rhs_.access_type);
    return result;
  endfunction
  
  // Custom convert2string
  virtual function string convert2string();
    string s;
    s = super.convert2string();
    s = {s, $sformatf("\n  Type: %s", access_type.name())};
    s = {s, $sformatf("\n  Addr: 0x%h", addr)};
    s = {s, $sformatf("\n  Data: 0x%h", data)};
    s = {s, $sformatf("\n  Strb: 0b%b", strb)};
    s = {s, $sformatf("\n  Delay: %0d", delay)};
    if (access_type == READ)
      s = {s, $sformatf("\n  Read Data: 0x%h", read_data)};
    s = {s, $sformatf("\n  Response: %0d", resp)};
    return s;
  endfunction
  
endclass
```

### 3.3 UVM Driver

```systemverilog
class axi_driver extends uvm_driver #(axi_transaction);
  
  `uvm_component_utils(axi_driver)
  
  // Virtual interface handle
  virtual axi4lite_if vif;
  
  // Constructor
  function new(string name = "axi_driver", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  // Build phase
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual axi4lite_if)::get(this, "", "vif", vif)) begin
      `uvm_fatal(get_type_name(), "Virtual interface not found in config DB")
    end
  endfunction
  
  // Run phase
  virtual task run_phase(uvm_phase phase);
    axi_transaction trans;
    
    // Initialize signals
    reset_signals();
    
    forever begin
      // Get transaction from sequencer
      seq_item_port.get_next_item(trans);
      
      `uvm_info(get_type_name(), 
                $sformatf("Driving transaction:\n%s", trans.sprint()),
                UVM_MEDIUM)
      
      // Drive transaction
      drive_transaction(trans);
      
      // Send response back
      seq_item_port.item_done();
    end
  endtask
  
  // Task to drive a transaction
  virtual task drive_transaction(axi_transaction trans);
    // Insert delay
    repeat(trans.delay) @(vif.cb);
    
    if (trans.access_type == axi_transaction::WRITE) begin
      drive_write(trans);
    end else begin
      drive_read(trans);
    end
  endtask
  
  // Write transaction
  virtual task drive_write(axi_transaction trans);
    // Drive write address
    @(vif.cb);
    vif.cb.awaddr  <= trans.addr;
    vif.cb.awprot  <= 3'b000;
    vif.cb.awvalid <= 1'b1;
    
    @(vif.cb iff vif.cb.awready);
    vif.cb.awvalid <= 1'b0;
    
    // Drive write data
    vif.cb.wdata  <= trans.data;
    vif.cb.wstrb  <= trans.strb;
    vif.cb.wvalid <= 1'b1;
    
    @(vif.cb iff vif.cb.wready);
    vif.cb.wvalid <= 1'b0;
    
    // Get write response
    vif.cb.bready <= 1'b1;
    @(vif.cb iff vif.cb.bvalid);
    trans.resp = vif.cb.bresp;
    @(vif.cb);
    vif.cb.bready <= 1'b0;
    
    `uvm_info(get_type_name(), 
              $sformatf("Write complete: addr=0x%h, data=0x%h, resp=%0d", 
                        trans.addr, trans.data, trans.resp),
              UVM_HIGH)
  endtask
  
  // Read transaction
  virtual task drive_read(axi_transaction trans);
    // Drive read address
    @(vif.cb);
    vif.cb.araddr  <= trans.addr;
    vif.cb.arprot  <= 3'b000;
    vif.cb.arvalid <= 1'b1;
    
    @(vif.cb iff vif.cb.arready);
    vif.cb.arvalid <= 1'b0;
    
    // Get read data
    vif.cb.rready <= 1'b1;
    @(vif.cb iff vif.cb.rvalid);
    trans.read_data = vif.cb.rdata;
    trans.resp      = vif.cb.rresp;
    @(vif.cb);
    vif.cb.rready <= 1'b0;
    
    `uvm_info(get_type_name(), 
              $sformatf("Read complete: addr=0x%h, data=0x%h, resp=%0d", 
                        trans.addr, trans.read_data, trans.resp),
              UVM_HIGH)
  endtask
  
  // Reset all signals
  virtual task reset_signals();
    vif.cb.awvalid <= 1'b0;
    vif.cb.wvalid  <= 1'b0;
    vif.cb.bready  <= 1'b0;
    vif.cb.arvalid <= 1'b0;
    vif.cb.rready  <= 1'b0;
  endtask
  
endclass
```

### 3.4 UVM Monitor

```systemverilog
class axi_monitor extends uvm_monitor;
  
  `uvm_component_utils(axi_monitor)
  
  // Virtual interface
  virtual axi4lite_if vif;
  
  // Analysis port to broadcast transactions
  uvm_analysis_port #(axi_transaction) ap;
  
  // Configuration
  bit checks_enable = 1;
  bit coverage_enable = 1;
  
  // Constructor
  function new(string name = "axi_monitor", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  // Build phase
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual axi4lite_if)::get(this, "", "vif", vif)) begin
      `uvm_fatal(get_type_name(), "Virtual interface not found")
    end
    ap = new("ap", this);
  endfunction
  
  // Run phase
  virtual task run_phase(uvm_phase phase);
    fork
      collect_write_transactions();
      collect_read_transactions();
    join_none
  endtask
  
  // Collect write transactions
  virtual task collect_write_transactions();
    axi_transaction trans;
    forever begin
      trans = axi_transaction::type_id::create("trans");
      trans.access_type = axi_transaction::WRITE;
      
      // Wait for write address valid
      @(vif.cb iff (vif.cb.awvalid && vif.cb.awready));
      trans.addr = vif.cb.awaddr;
      
      // Capture write data
      @(vif.cb iff (vif.cb.wvalid && vif.cb.wready));
      trans.data = vif.cb.wdata;
      trans.strb = vif.cb.wstrb;
      
      // Capture write response
      @(vif.cb iff (vif.cb.bvalid && vif.cb.bready));
      trans.resp = vif.cb.bresp;
      
      `uvm_info(get_type_name(), 
                $sformatf("Monitored Write:\n%s", trans.sprint()),
                UVM_MEDIUM)
      
      // Broadcast transaction
      ap.write(trans);
      
      // Protocol checks
      if (checks_enable) begin
        check_write_protocol(trans);
      end
    end
  endtask
  
  // Collect read transactions
  virtual task collect_read_transactions();
    axi_transaction trans;
    forever begin
      trans = axi_transaction::type_id::create("trans");
      trans.access_type = axi_transaction::READ;
      
      // Wait for read address valid
      @(vif.cb iff (vif.cb.arvalid && vif.cb.arready));
      trans.addr = vif.cb.araddr;
      
      // Capture read data
      @(vif.cb iff (vif.cb.rvalid && vif.cb.rready));
      trans.read_data = vif.cb.rdata;
      trans.resp      = vif.cb.rresp;
      
      `uvm_info(get_type_name(), 
                $sformatf("Monitored Read:\n%s", trans.sprint()),
                UVM_MEDIUM)
      
      // Broadcast transaction
      ap.write(trans);
      
      // Protocol checks
      if (checks_enable) begin
        check_read_protocol(trans);
      end
    end
  endtask
  
  // Protocol checker for write
  virtual function void check_write_protocol(axi_transaction trans);
    // Check response is OKAY or SLVERR
    if (!(trans.resp inside {2'b00, 2'b10})) begin
      `uvm_error(get_type_name(), 
                 $sformatf("Invalid write response: %0d", trans.resp))
    end
    
    // Check address alignment
    if (trans.addr[1:0] != 2'b00) begin
      `uvm_error(get_type_name(), 
                 $sformatf("Unaligned write address: 0x%h", trans.addr))
    end
  endfunction
  
  // Protocol checker for read
  virtual function void check_read_protocol(axi_transaction trans);
    // Check response
    if (!(trans.resp inside {2'b00, 2'b10})) begin
      `uvm_error(get_type_name(), 
                 $sformatf("Invalid read response: %0d", trans.resp))
    end
    
    // Check address alignment
    if (trans.addr[1:0] != 2'b00) begin
      `uvm_error(get_type_name(), 
                 $sformatf("Unaligned read address: 0x%h", trans.addr))
    end
  endfunction
  
endclass
```

### 3.5 UVM Sequencer and Sequences

```systemverilog
// Sequencer (typically no customization needed)
class axi_sequencer extends uvm_sequencer #(axi_transaction);
  
  `uvm_component_utils(axi_sequencer)
  
  function new(string name = "axi_sequencer", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
endclass

// Base sequence
class axi_base_sequence extends uvm_sequence #(axi_transaction);
  
  `uvm_object_utils(axi_base_sequence)
  
  function new(string name = "axi_base_sequence");
    super.new(name);
  endfunction
  
  // Pre-body: called before body
  virtual task pre_body();
    if (starting_phase != null) begin
      starting_phase.raise_objection(this, $sformatf("%s raise objection", get_type_name()));
    end
  endtask
  
  // Post-body: called after body
  virtual task post_body();
    if (starting_phase != null) begin
      starting_phase.drop_objection(this, $sformatf("%s drop objection", get_type_name()));
    end
  endtask
  
endclass

// Single write sequence
class axi_write_sequence extends axi_base_sequence;
  
  `uvm_object_utils(axi_write_sequence)
  
  rand bit [31:0] addr;
  rand bit [31:0] data;
  
  function new(string name = "axi_write_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    axi_transaction trans;
    
    trans = axi_transaction::type_id::create("trans");
    
    start_item(trans);
    assert(trans.randomize() with {
      access_type == axi_transaction::WRITE;
      addr == local::addr;
      data == local::data;
    });
    finish_item(trans);
    
    get_response(trans);
    
    `uvm_info(get_type_name(), 
              $sformatf("Write sequence completed: addr=0x%h, data=0x%h, resp=%0d",
                        trans.addr, trans.data, trans.resp),
              UVM_LOW)
  endtask
  
endclass

// Single read sequence
class axi_read_sequence extends axi_base_sequence;
  
  `uvm_object_utils(axi_read_sequence)
  
  rand bit [31:0] addr;
  bit [31:0] read_data;
  
  function new(string name = "axi_read_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    axi_transaction trans;
    
    trans = axi_transaction::type_id::create("trans");
    
    start_item(trans);
    assert(trans.randomize() with {
      access_type == axi_transaction::READ;
      addr == local::addr;
    });
    finish_item(trans);
    
    get_response(trans);
    read_data = trans.read_data;
    
    `uvm_info(get_type_name(), 
              $sformatf("Read sequence completed: addr=0x%h, data=0x%h, resp=%0d",
                        trans.addr, trans.read_data, trans.resp),
              UVM_LOW)
  endtask
  
endclass

// Burst sequence
class axi_burst_sequence extends axi_base_sequence;
  
  `uvm_object_utils(axi_burst_sequence)
  
  rand int num_transactions;
  rand bit [31:0] start_addr;
  
  constraint reasonable_burst {
    num_transactions inside {[4:16]};
  }
  
  function new(string name = "axi_burst_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    axi_transaction trans;
    
    for (int i = 0; i < num_transactions; i++) begin
      trans = axi_transaction::type_id::create($sformatf("trans_%0d", i));
      
      start_item(trans);
      assert(trans.randomize() with {
        addr == start_addr + (i * 4);
      });
      finish_item(trans);
      
      get_response(trans);
    end
    
    `uvm_info(get_type_name(), 
              $sformatf("Burst sequence of %0d transactions completed", num_transactions),
              UVM_LOW)
  endtask
  
endclass

// Random sequence
class axi_random_sequence extends axi_base_sequence;
  
  `uvm_object_utils(axi_random_sequence)
  
  rand int num_transactions;
  
  constraint reasonable_num {
    num_transactions inside {[10:50]};
  }
  
  function new(string name = "axi_random_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    axi_transaction trans;
    
    for (int i = 0; i < num_transactions; i++) begin
      trans = axi_transaction::type_id::create($sformatf("trans_%0d", i));
      
      start_item(trans);
      assert(trans.randomize());
      finish_item(trans);
      
      get_response(trans);
    end
    
    `uvm_info(get_type_name(), 
              $sformatf("Random sequence of %0d transactions completed", num_transactions),
              UVM_LOW)
  endtask
  
endclass

// Write-Read-Compare sequence
class axi_wr_rd_compare_sequence extends axi_base_sequence;
  
  `uvm_object_utils(axi_wr_rd_compare_sequence)
  
  rand bit [31:0] addr;
  rand bit [31:0] write_data;
  
  function new(string name = "axi_wr_rd_compare_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    axi_write_sequence wr_seq;
    axi_read_sequence  rd_seq;
    
    // Write
    wr_seq = axi_write_sequence::type_id::create("wr_seq");
    wr_seq.addr = addr;
    wr_seq.data = write_data;
    wr_seq.start(m_sequencer);
    
    // Read
    rd_seq = axi_read_sequence::type_id::create("rd_seq");
    rd_seq.addr = addr;
    rd_seq.start(m_sequencer);
    
    // Compare
    if (rd_seq.read_data == write_data) begin
      `uvm_info(get_type_name(), 
                $sformatf("WR-RD-CMP PASS: addr=0x%h, data=0x%h", addr, write_data),
                UVM_LOW)
    end else begin
      `uvm_error(get_type_name(), 
                 $sformatf("WR-RD-CMP FAIL: addr=0x%h, wr=0x%h, rd=0x%h", 
                           addr, write_data, rd_seq.read_data))
    end
  endtask
  
endclass
```

### 3.6 UVM Agent

```systemverilog
class axi_agent extends uvm_agent;
  
  `uvm_component_utils(axi_agent)
  
  // Agent components
  axi_sequencer sequencer;
  axi_driver    driver;
  axi_monitor   monitor;
  
  // Configuration
  axi_agent_config cfg;
  
  // Analysis port from monitor
  uvm_analysis_port #(axi_transaction) ap;
  
  // Constructor
  function new(string name = "axi_agent", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  // Build phase
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    
    // Get configuration
    if (!uvm_config_db#(axi_agent_config)::get(this, "", "cfg", cfg)) begin
      `uvm_info(get_type_name(), "Using default agent configuration", UVM_MEDIUM)
      cfg = axi_agent_config::type_id::create("cfg");
    end
    
    // Create monitor (always created)
    monitor = axi_monitor::type_id::create("monitor", this);
    
    // Create sequencer and driver if active
    if (cfg.is_active == UVM_ACTIVE) begin
      sequencer = axi_sequencer::type_id::create("sequencer", this);
      driver    = axi_driver::type_id::create("driver", this);
    end
    
    // Set configuration for children
    uvm_config_db#(axi_agent_config)::set(this, "*", "cfg", cfg);
  endfunction
  
  // Connect phase
  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    
    // Connect driver to sequencer
    if (cfg.is_active == UVM_ACTIVE) begin
      driver.seq_item_port.connect(sequencer.seq_item_export);
    end
    
    // Connect monitor's analysis port to agent's analysis port
    ap = monitor.ap;
  endfunction
  
endclass

// Agent configuration object
class axi_agent_config extends uvm_object;
  
  `uvm_object_utils(axi_agent_config)
  
  // Configuration parameters
  uvm_active_passive_enum is_active = UVM_ACTIVE;
  bit has_scoreboard = 1;
  bit has_coverage   = 1;
  
  // Virtual interface
  virtual axi4lite_if vif;
  
  function new(string name = "axi_agent_config");
    super.new(name);
  endfunction
  
endclass
```

### 3.7 UVM Scoreboard

```systemverilog
class axi_scoreboard extends uvm_scoreboard;
  
  `uvm_component_utils(axi_scoreboard)
  
  // Analysis imports (TLM ports)
  uvm_analysis_imp_pred #(axi_transaction, axi_scoreboard) predictor_imp;
  uvm_analysis_imp_mon  #(axi_transaction, axi_scoreboard) monitor_imp;
  
  // Internal storage
  axi_transaction expected_queue[$];
  axi_transaction actual_queue[$];
  
  // Statistics
  int match_count;
  int mismatch_count;
  int dropped_count;
  
  // Memory model for write-read checking
  bit [31:0] memory [bit[31:0]];
  
  // Constructor
  function new(string name = "axi_scoreboard", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  // Build phase
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    predictor_imp = new("predictor_imp", this);
    monitor_imp   = new("monitor_imp", this);
  endfunction
  
  // Write method for predictor (expected transactions)
  virtual function void write_pred(axi_transaction trans);
    axi_transaction exp_trans;
    $cast(exp_trans, trans.clone());
    
    `uvm_info(get_type_name(), 
              $sformatf("Predictor transaction received:\n%s", exp_trans.sprint()),
              UVM_HIGH)
    
    // Update internal memory model
    if (trans.access_type == axi_transaction::WRITE) begin
      memory[trans.addr] = trans.data;
    end else begin
      // For reads, set expected read data from memory
      if (memory.exists(trans.addr))
        exp_trans.read_data = memory[trans.addr];
      else
        exp_trans.read_data = 32'h0; // Default value
    end
    
    expected_queue.push_back(exp_trans);
  endfunction
  
  // Write method for monitor (actual transactions)
  virtual function void write_mon(axi_transaction trans);
    axi_transaction act_trans;
    $cast(act_trans, trans.clone());
    
    `uvm_info(get_type_name(), 
              $sformatf("Monitor transaction received:\n%s", act_trans.sprint()),
              UVM_HIGH)
    
    actual_queue.push_back(act_trans);
    compare_transactions();
  endfunction
  
  // Compare transactions
  virtual function void compare_transactions();
    axi_transaction exp_trans, act_trans;
    
    if (expected_queue.size() > 0 && actual_queue.size() > 0) begin
      exp_trans = expected_queue.pop_front();
      act_trans = actual_queue.pop_front();
      
      if (exp_trans.compare(act_trans)) begin
        match_count++;
        `uvm_info(get_type_name(), 
                  $sformatf("MATCH #%0d: addr=0x%h", match_count, act_trans.addr),
                  UVM_MEDIUM)
      end else begin
        mismatch_count++;
        `uvm_error(get_type_name(), 
                   $sformatf("MISMATCH #%0d:\nExpected:\n%s\nActual:\n%s",
                             mismatch_count, exp_trans.sprint(), act_trans.sprint()))
      end
    end
  endfunction
  
  // Check phase - final checking
  virtual function void check_phase(uvm_phase phase);
    super.check_phase(phase);
    
    if (expected_queue.size() != 0) begin
      `uvm_error(get_type_name(), 
                 $sformatf("%0d expected transactions remain in queue", expected_queue.size()))
    end
    
    if (actual_queue.size() != 0) begin
      `uvm_error(get_type_name(), 
                 $sformatf("%0d actual transactions remain in queue", actual_queue.size()))
    end
  endfunction
  
  // Report phase - print statistics
  virtual function void report_phase(uvm_phase phase);
    super.report_phase(phase);
    
    `uvm_info(get_type_name(), 
              $sformatf("\n========== Scoreboard Statistics ==========\n\
                         Matches:    %0d\n\
                         Mismatches: %0d\n\
                         Dropped:    %0d\n\
                         ===========================================",
                        match_count, mismatch_count, dropped_count),
              UVM_NONE)
  endfunction
  
endclass
```

*(Continuing with sections 3.8-3.10, then 4-18 with detailed examples...)*

**Due to length constraints, I'll continue in the next sections. Would you like me to:**

1. **Continue with remaining UVM sections** (Environment, Tests, Virtual Sequences)
2. **Move to Testbench Architecture** (Section 4)
3. **Jump to specific topics** like Assertions, Coverage, or Debug?

**The document structure continues with:**
- Section 3.8: UVM Environment
- Section 3.9: UVM Test
- Section 3.10: UVM Configuration and Factory
- Sections 4-18: All remaining topics with hands-on examples

**Should I continue adding the remaining sections to this file?**

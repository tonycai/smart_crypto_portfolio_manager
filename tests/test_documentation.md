# Smart Crypto Portfolio Manager - Test Documentation

## Overview

This document outlines the testing strategy and test cases for the Smart Crypto Portfolio Manager system. The test suite validates various aspects of the system, including workflow functionality, agent-to-agent communication, and LLM integration.

## Test Categories

The test suite is divided into the following categories:

1. **Workflow Tests**: Tests for the crypto order workflow and other workflows
2. **Agent-to-Agent Protocol Tests**: Tests for the communication protocol between agents
3. **LLM Integration Tests**: Tests for integration with LLM models via function calls
4. **Agent Integration Tests**: Tests for integration between workflows and specific agents

## 1. Workflow Tests

### 1.1 Crypto Order Workflow Tests (`test_crypto_order_workflow.py`)

Tests both the legacy and object-oriented implementations of the crypto order workflow.

#### Legacy Implementation Tests

| Test Name | Description | Verification Points |
|-----------|-------------|---------------------|
| `test_get_workflow_market_order` | Tests creating a market order workflow | Verifies workflow creation, step sequence, and parameters |
| `test_get_workflow_limit_order` | Tests creating a limit order workflow | Verifies parameters specific to limit orders |
| `test_get_workflow_missing_required_params` | Tests error handling for missing parameters | Verifies appropriate error messages |
| `test_get_workflow_invalid_order_type` | Tests handling of invalid order types | Verifies proper validation and error messages |
| `test_get_workflow_invalid_side` | Tests handling of invalid order sides | Verifies proper validation and error messages |
| `test_get_workflow_invalid_amount` | Tests handling of invalid amounts | Verifies validation for negative and non-numeric amounts |
| `test_get_workflow_limit_order_missing_price` | Tests limit orders without price | Verifies price requirement validation |

#### Step Simulation Tests

| Test Name | Description | Verification Points |
|-----------|-------------|---------------------|
| `test_simulate_step_execution_validate_order_params` | Tests order parameter validation step | Verifies validation results and status |
| `test_simulate_step_execution_check_available_funds` | Tests funds availability check step | Verifies funds check results |
| `test_simulate_step_execution_calculate_order_details` | Tests order details calculation step | Verifies calculation of crypto amount, USD amount, etc. |
| `test_simulate_step_execution_submit_order` | Tests order submission step | Verifies order submission status and details |
| `test_simulate_step_execution_monitor_order_status` | Tests order status monitoring step | Verifies order status tracking |
| `test_simulate_step_execution_update_portfolio` | Tests portfolio update step | Verifies portfolio balance changes |

#### OOP Implementation Tests

| Test Name | Description | Verification Points |
|-----------|-------------|---------------------|
| `test_create_workflow` | Tests workflow creation via helper function | Verifies workflow structure |
| `test_workflow_init_and_steps` | Tests direct initialization and step structure | Verifies workflow properties and steps |
| `test_validate_parameters_valid` | Tests parameter validation with valid inputs | Verifies successful validation |
| `test_validate_parameters_invalid` | Tests parameter validation with invalid inputs | Verifies rejection of invalid parameters |
| `test_*_step` | Tests individual steps in OOP implementation | Verifies functionality of each step |
| `test_execute_all_steps` | Tests execution of the entire workflow | Verifies complete workflow execution |

## 2. Agent-to-Agent Protocol Tests (`test_agent_to_agent_protocol.py`)

Tests the communication protocol between different agents in the system.

### Message Structure and Flow Tests

| Test Name | Description | Verification Points |
|-----------|-------------|---------------------|
| `test_a2a_basic_message_structure` | Tests basic message format | Verifies required fields and structure for both requests and responses |
| `test_a2a_market_analysis_request` | Tests market analysis agent protocol | Verifies risk assessment request/response format |
| `test_a2a_trade_execution_request` | Tests trade execution agent protocol | Verifies trade execution request/response format |
| `test_a2a_portfolio_update_request` | Tests portfolio agent protocol | Verifies portfolio update request/response format |
| `test_a2a_risk_assessment_request` | Tests risk management agent protocol | Verifies risk assessment request/response format |

### Advanced Protocol Tests

| Test Name | Description | Verification Points |
|-----------|-------------|---------------------|
| `test_a2a_request_chain` | Tests a chain of agent-to-agent requests | Verifies multi-step workflow across agents |
| `test_a2a_error_handling` | Tests error response handling | Verifies error structure and codes |
| `test_a2a_idempotency` | Tests idempotency with duplicate messages | Verifies consistent results with same message ID |

## 3. LLM Integration Tests (`test_llm_crypto_order_integration.py`)

Tests the integration of LLM models with the system via function calls to the MCP client and server.

### LLM Function Tests

| Test Name | Description | Verification Points |
|-----------|-------------|---------------------|
| `test_llm_function_check_agents_status` | Tests LLM function for checking agent status | Verifies agent status retrieval |
| `test_llm_function_create_market_order` | Tests LLM function for creating market orders | Verifies market order creation parameters |
| `test_llm_function_create_limit_order` | Tests LLM function for creating limit orders | Verifies limit order creation parameters |
| `test_llm_function_check_order_status` | Tests LLM function for checking order status | Verifies order status tracking |
| `test_llm_function_get_order_result` | Tests LLM function for retrieving order results | Verifies detailed order result retrieval |
| `test_llm_function_cancel_order` | Tests LLM function for canceling orders | Verifies order cancellation |

### Conversation Flow Tests

| Test Name | Description | Verification Points |
|-----------|-------------|---------------------|
| `test_llm_conversation_market_order_flow` | Tests a complete conversation flow for market orders | Verifies end-to-end conversation flow |

## 4. Agent Integration Tests (`test_crypto_order_agent_integration.py`)

Tests the integration between the crypto order workflow and system agents.

### Agent Integration Tests

| Test Name | Description | Verification Points |
|-----------|-------------|---------------------|
| `test_market_analysis_agent_integration` | Tests integration with market analysis agent | Verifies risk assessment capabilities |
| `test_trade_execution_agent_integration` | Tests integration with trade execution agent | Verifies order execution functionality |
| `test_trade_execution_agent_order_status` | Tests order status checking via trade agent | Verifies order status tracking |
| `test_risk_management_agent_integration` | Tests integration with risk management agent | Verifies trade risk assessment |
| `test_reporting_agent_portfolio_update` | Tests integration with reporting agent | Verifies portfolio updates |

### Workflow Integration Tests

| Test Name | Description | Verification Points |
|-----------|-------------|---------------------|
| `test_workflow_with_market_analysis_risk_check` | Tests workflow step with market analysis | Verifies risk assessment step |
| `test_complete_order_workflow_simulation` | Tests complete order workflow | Verifies end-to-end workflow execution |

## Running the Tests

To run the tests, use the following command from the project root:

```bash
python -m unittest discover tests
```

To run a specific test file:

```bash
python -m unittest tests/test_crypto_order_workflow.py
```

To run a specific test class:

```bash
python -m unittest tests.test_crypto_order_workflow.TestCryptoOrderWorkflowLegacy
```

To run a specific test method:

```bash
python -m unittest tests.test_crypto_order_workflow.TestCryptoOrderWorkflowLegacy.test_get_workflow_market_order
```

## Mocking Strategy

The test suite extensively uses Python's `unittest.mock` library to mock external dependencies:

1. **HTTP Requests**: All external HTTP requests are mocked using `patch('requests.post')` and `MockResponse` class
2. **Subprocess Calls**: System calls to the MCP client are mocked using `patch('subprocess.run')`
3. **Order IDs and UUIDs**: Deterministic UUIDs are created for testing using `uuid.uuid4()`
4. **Timestamps**: Current timestamps are generated using `datetime.utcnow().isoformat()`

## Test Data

Test data includes:

1. **Sample Orders**: Market and limit orders for various cryptocurrencies
2. **Agent Endpoints**: URLs for different system agents
3. **Mock Responses**: Predefined response patterns for different scenarios

## Code Coverage

Test coverage focuses on:

1. **Functional Coverage**: All core functions and methods are tested
2. **Error Handling**: All error conditions and edge cases are tested
3. **Integration Paths**: All integration points between components are tested
4. **End-to-End Flows**: Complete workflows are tested from start to finish 
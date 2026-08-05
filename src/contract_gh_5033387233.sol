// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title SolutionContract_gh_5033387233
 * @notice Contrato inteligente Solidity para el bounty: RWA Tokenization Demo & Contract Tests
 */
contract SolutionContract_gh_5033387233 {
    address public owner;
    mapping(address => uint256) public balances;

    event Deposited(address indexed sender, uint256 amount);

    constructor() {
        owner = msg.sender;
    }

    function deposit() external payable {
        require(msg.value > 0, "Monto invalido");
        balances[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }
}

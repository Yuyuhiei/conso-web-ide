import React from 'react';

const TokenTable = ({ tokens }) => {
  if (!tokens || tokens.length === 0) {
    return (
      <div className="token-table-container">
        <div className="token-table-header">Lexical Analysis</div>
        <div className="token-table-empty">No tokens to display</div>
      </div>
    );
  }

  return (
    <div className="token-table-container">
      <div className="token-table-header">Lexical Analysis</div>
      <div className="token-table-content">
        <table>
          <thead>
            <tr>
              <th>Lexeme</th>
              <th>Token</th>
            </tr>
          </thead>
          <tbody>
            {tokens.map((token, index) => (
              <tr key={index}>
                <td>{token.value}</td>
                <td>{token.type}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TokenTable;
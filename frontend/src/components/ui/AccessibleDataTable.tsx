import React from 'react';

export interface AccessibleDataTableProps {
  caption: string;
  headers: string[];
  rows: (string | number)[][];
}

export const AccessibleDataTable: React.FC<AccessibleDataTableProps> = ({ caption, headers, rows }) => {
  return (
    <div className="sr-only">
      <table aria-label={caption}>
        <caption>{caption}</caption>
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={i} scope="col">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rIdx) => (
            <tr key={rIdx}>
              {row.map((cell, cIdx) => (
                <td key={cIdx}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

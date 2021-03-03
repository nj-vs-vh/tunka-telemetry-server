import React from 'react';

import './index.css'

const TextWithIcon = ({ icon, children }) => (
  <div className="icon-with-text">
    <img src={icon} className="icon" alt=""></img>
    <span className="bartext">{children}</span>
  </div>
);

export default TextWithIcon;

import React, { useState, useEffect } from 'react';

export default function App() {
  const [count, setCount] = useState(10);
  const [isCounting, setIsCounting] = useState(false);

  useEffect(() => {
    let timer;
    if (isCounting && count > 0) {
      timer = setInterval(() => {
        setCount(prev => prev - 1);
      }, 1000);
    }

    if (count === 0 && isCounting) {
      setIsCounting(false);
      alert('倒數結束！');
    }

    return () => clearInterval(timer);
  }, [isCounting, count]);

  const startCountdown = () => {
    if (!isCounting) {
      setCount(10);
      setIsCounting(true);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      flexDirection: 'column',
      height: '100vh',   // ✨ 保證佔滿高度
      width: '100vw',    // ✨ 保證佔滿寬度
      background: '#222', // 可有可無，讓你更明顯看出居中
    }}>
      <h1 style={{ color: '#fff' }}>{count}</h1>
      <button onClick={startCountdown} disabled={isCounting} style={{
        padding: '10px 20px',
        marginTop: '20px',
        fontSize: '20px',
        cursor: 'pointer'
      }}>
        START
      </button>
    </div>
  );
}
import { useState, useRef, useCallback, useEffect } from 'react';

const API_BASE = 'http://localhost:8000/api';
const WS_BASE = 'ws://localhost:8000/api/ws/tasks';

export function useTaskRunner() {
  const [task, setTask] = useState(null);
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState('idle'); // 'idle' | 'running' | 'awaiting_approval' | 'completed' | 'failed'
  const [error, setError] = useState(null);
  const [approvalRequest, setApprovalRequest] = useState(null);
  const [verificationResult, setVerificationResult] = useState(null);
  const [backendHealth, setBackendHealth] = useState(null);

  const socketRef = useRef(null);

  // Check backend health
  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8000/health');
      if (res.ok) {
        const data = await res.json();
        setBackendHealth(data);
      }
    } catch {
      setBackendHealth({ status: 'offline' });
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  const startTask = useCallback(async (goalText) => {
    setError(null);
    setEvents([]);
    setVerificationResult(null);
    setApprovalRequest(null);
    setStatus('running');

    try {
      // 1. Create task via REST
      const res = await fetch(`${API_BASE}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: goalText }),
      });

      if (!res.ok) {
        throw new Error(`Failed to create task (${res.status})`);
      }

      const newTask = await res.json();
      setTask(newTask);

      // 2. Open WebSocket stream
      if (socketRef.current) {
        socketRef.current.close();
      }

      const ws = new WebSocket(`${WS_BASE}/${newTask.task_id}`);
      socketRef.current = ws;

      ws.onopen = () => {
        // Stream connected
      };

      ws.onmessage = (e) => {
        const event = JSON.parse(e.data);
        setEvents((prev) => [...prev, event]);

        if (event.event_type === 'approval_needed') {
          setStatus('awaiting_approval');
          setApprovalRequest(event);
        } else if (event.event_type === 'verification_result') {
          setVerificationResult(event.data);
        } else if (event.event_type === 'task_complete') {
          setStatus('completed');
          if (event.data?.verification) {
            setVerificationResult(event.data.verification);
          }
        } else if (event.event_type === 'task_failed') {
          setStatus('failed');
          setError(event.message);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('Connection to agent task stream failed.');
        setStatus('failed');
      };

      ws.onclose = () => {
        // Closed
      };
    } catch (err) {
      console.error(err);
      setError(err.message);
      setStatus('failed');
    }
  }, []);

  const sendApproval = useCallback(
    async (approved) => {
      if (!task) return;

      // Send over WebSocket if open, fallback to REST
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(
          JSON.stringify({ action: 'approval', approved })
        );
      } else {
        await fetch(`${API_BASE}/tasks/${task.task_id}/approval`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ approved, message: approved ? 'Approved' : 'Rejected' }),
        });
      }

      setApprovalRequest(null);
      if (approved) {
        setStatus('running');
      } else {
        setStatus('failed');
      }
    },
    [task]
  );

  const resetAll = useCallback(async () => {
    if (socketRef.current) {
      socketRef.current.close();
    }
    setTask(null);
    setEvents([]);
    setStatus('idle');
    setError(null);
    setApprovalRequest(null);
    setVerificationResult(null);

    try {
      await fetch(`${API_BASE}/reset`, { method: 'POST' });
    } catch (e) {
      console.error('Reset failed:', e);
    }
  }, []);

  return {
    task,
    events,
    status,
    error,
    approvalRequest,
    verificationResult,
    backendHealth,
    startTask,
    sendApproval,
    resetAll,
  };
}

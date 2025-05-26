import React, { useState } from 'react';
import axios from 'axios';
import './SalaryLogsComponents.css'

const SalaryLogsComponent = ({ state, dispatch, API_URL }) => {
    const [showLogs, setShowLogs] = useState(false);

    const fetchData = async (endpoint, params, resultField) => {
        try {
            const response = await axios.get(`${API_URL}/${endpoint}`, {
                params,
                headers: { 'Content-Type': 'application/json' },
            });
            dispatch({ type: "SET_RESULT", field: resultField, value: response.data });
            setShowLogs(true); // Show after fetch
        } catch (error) {
            console.error("Error:", error);
        }
    };

    return (
        <div className="salary-logs">
            <h3>Salary Change Logs</h3>
            <button onClick={() => fetchData("get_salary_logs", {}, "salaryLogs")}>
                Fetch Logs
            </button>
            {showLogs && (
                <div className='logs'>
                    <ul>
                        {state.salaryLogs.map((log, index) => (
                            <li key={index}>
                                {log.emp_id} - ${log.old_salary} → ${log.new_salary}
                            </li>
                        ))}
                    </ul>
                    <div className="logsButton" onClick={() => {
                        setShowLogs(false);
                        dispatch({ type: "SET_RESULT", field: "salaryLogs", value: [] });
                    }} style={{ marginTop: '10px' }}>
                        <span className="X"></span>
                        <span className="Y"></span>
                        <div className="close">Close</div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SalaryLogsComponent;
import { useState, useEffect, useReducer } from "react";
import axios from "axios";
import "./App.css";
import { Slide, toast, ToastContainer } from 'react-toastify';
import SalaryLogsComponent from './SalaryLogsComponent';


const API_URL = "https://user-management-wucu.onrender.com";

const initialState = {
    num1: "",
    num2: "",
    sumResults: null,
    squareNumber: "",
    squareResult: null,
    celsius: "",
    farenheitResult: null,
    checkNumber: "",
    evenOddResult: null,
    salaryThreshold: "",
    highSalaryEmployees: [],
    empId: "",
    employeeSalary: null,
    emp_id_bonus: "",
    bonus: null,
    update_emp_id: "",
    newSalary: "",
    salaryUpdateResponse: null,
    salaryLogs: [],
    emp_name: "",
    emp_salary: "",
    addEmployeeResult: null,
    salaryIncreasePercent: "",
    salaryIncreasePercentResponse: null
}

function reducer(state, action) {
    switch (action.type) {
        case "SET_INPUT":
            return { ...state, [action.field]: action.value };
        case "SET_RESULT":
            console.log("Updating state:", action.field, action.value);
            return { ...state, [action.field]: action.value };
        default:
            return state;
    }
}

function Home() {
    const [users, setUsers] = useState([]);
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [editId, setEditId] = useState(null);
    const [loading, setLoading] = useState(false);
    const [loadingAdd, setLoadingAdd] = useState(false);
    const [loadingUpdate, setLoadingUpdate] = useState(false);
    const [loadingSum, setLoadingSum] = useState(false);
    const [loadingSquare, setLoadingSquare] = useState(false);
    const [loadingEvenOdd, setLoadingEvenOdd] = useState(false);
    const [loadingTemperature, setLoadingTemperature] = useState(false);
    const [loadingSalThres, setLoadingSalThres] = useState(false);
    const [loadingSalary, setLoadingSalary] = useState(false);
    const [loadingBonus, setLoadingBonus] = useState(false);
    const [loadingUpdateSal, setLoadingUpdateSal] = useState(false);
    const [loadingAddEmp, setLoadingAddEmp] = useState(false);
    const [loadingSalaryIncreasePercent, setLoadingSalaryIncreasePercent] = useState(false);

    useEffect(() => {
        fetchUsers();
    }, []);

    const API_URL_CRUD = "https://user-management-wucu.onrender.com/users";

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${API_URL_CRUD}`);
            console.log("API Response:", response.data); // Debugging

            if (Array.isArray(response.data)) {
                setUsers(response.data);
            } else if (response.data && Array.isArray(response.data.users)) {
                // If API wraps users inside an object
                setUsers(response.data.users);
            } else {
                console.error("Unexpected API response format", response.data);
                setUsers([]); // Fallback to empty array
            }
        } catch (error) {
            console.error("Error fetching users:", error);
            setUsers([]); // Ensure it's always an array
        } finally {
            setLoading(false);
        }
    };


    // const fetchUsers = async () => {
    //   try {
    //     const response = await axios.get(API_URL);
    //     // console.log("Users fetched:", response.data);
    //     setUsers(response.data);
    //   } catch (error) {
    //     console.error("Error fetching users:", error);
    //   }
    // };

    const createUser = async (e) => {
        e.preventDefault();
        if (!name || !email) {
            toast.warn("Please fill in all fields.");
            return;
        }
        setLoadingAdd(true);
        try {
            const response = await axios.post(`${API_URL_CRUD}`, { name, email });
            setUsers([...users, response.data]);
            setName("");
            setEmail("");
            toast.success("User created successfully!");
        } catch (error) {
            if (error.response && error.response.status === 409) {
                toast.error("User already exists!");
            } else {
                toast.error("Error creating user.");
            }
        } finally {
            setLoadingAdd(false);
        }
    };

    const updateUser = async (e) => {
        e.preventDefault();
        setLoadingUpdate(true);
        if (!name && !email) {
            toast.warn("Please fill in at least one field.");
            return;
        }

        try {
            const response = await axios.put(`${API_URL_CRUD}/${editId}`, { name, email });
            setUsers(users.map((user) => (user.id === editId ? response.data : user)));
            setName("");
            setEmail("");
            setEditId(null);
            toast.success("User updated successfully!");
        } catch (error) {
            toast.error("Error updating user.");
        } finally {
            setLoadingUpdate(false);
        }
    };

    const deleteUser = async (id) => {
        if (!id) {
            console.error("User ID is undefined");
            return;
        }
        try {
            const response = await axios.delete(`${API_URL_CRUD}/${id}`);
            console.log("Delete response:", response);

            if (response.status === 200) {
                setUsers(users.filter(user => user.id !== id));
                toast.success("User deleted successfully!");
            }
        } catch (error) {
            console.error("Error deleting user:", error);
            toast.error("Failed to delete user. Please try again.");
        } finally {
        }
    };

    const [state, dispatch] = useReducer(reducer, initialState);

    const postData = async (endpoint, data, resultField) => {
        switch (endpoint) {
            case 'add_numbers':
                setLoadingSum(true);
                break;
            case 'celsius_to_fahrenheit':
                setLoadingTemperature(true);
                break;
            case 'add_employee':
                setLoadingAddEmp(true);
                break;
            case 'increase_all_salaries':
                setLoadingSalaryIncreasePercent(true);
                break;
            default:
                break;
        }
        try {
            const response = await axios.post(`${API_URL}/${endpoint}`, data,
                {
                    headers: { 'Content-Type': 'application/json' },
                });
            console.log("Response:", response);
            console.log("API Response:", response.data);
            dispatch({ type: "SET_RESULT", field: resultField, value: response.data });
            toast.success(response.data.message || "Data posted successfully!", { position: "top-center" });
            return response.data;
        } catch (error) {
            console.error("API Error:", error);
            toast.error("API Error:", error);
        } finally {
            switch (endpoint) {
                case 'add_numbers':
                    setLoadingSum(false);
                    break;
                case 'celsius_to_fahrenheit':
                    setLoadingTemperature(false);
                    break;
                case 'add_employee':
                    setLoadingAddEmp(false);
                    break;
                case 'increase_all_salaries':
                    setLoadingSalaryIncreasePercent(false);
                    break;
                default:
                    break;
            }
        }
    }

    const fetchData = async (endpoint, params, resultField) => {
        const baseEndpoint = endpoint.split('/')[0];
        switch (baseEndpoint) {
            case 'square':
                setLoadingSquare(true);
                break;
            case 'check_even_odd':
                setLoadingEvenOdd(true);
                break;
            case 'get_employee_salary':
                setLoadingSalary(true);
                break;
            case 'calculate_bonus':
                setLoadingBonus(true);
                break;
            default:
                break;
        }

        try {
            const response = await axios.get(`${API_URL}/${endpoint}`, { params },
                {
                    headers: { 'Content-Type': 'application/json' },
                });
            console.log("Response:", response);
            console.log("API Response:", response.data);
            console.log("Updating state:", resultField, response.data);
            dispatch({ type: "SET_RESULT", field: resultField, value: response.data });
            return response.data;
        } catch (error) {
            console.error("Error:", error);
        } finally {
            switch (baseEndpoint) {
                case 'square':
                    setLoadingSquare(false);
                    break;
                case 'check_even_odd':
                    setLoadingEvenOdd(false);
                    break;
                case 'get_employee_salary':
                    setLoadingSalary(false);
                    break;
                case 'calculate_bonus':
                    setLoadingBonus(false);
                    break;
                default:
                    break;
            }
        }
    }

    // const putData = async (endpoint, data, resultField) => {
    //   try {
    //     const response = await axios.put(`${API_URL}/${endpoint}`, data);
    //     dispatch({ type: "SET_RESULT", field: resultField, value: response.data });
    //   } catch (error) {
    //     console.error("Error:", error);
    //   }
    // }

    const putData = async (endpoint, data, resultField) => {
        setLoadingUpdateSal(true);
        try {
            const response = await axios.put(`${API_URL}/${endpoint}`, data, {
                headers: { "Content-Type": "application/json" }
            });
            console.log("Response:", response);
            console.log("API Response:", response.data);
            console.log("Updating state:", resultField, response.data);
            dispatch({ type: "SET_RESULT", field: resultField, value: response.data });
            toast.success(response.data.message || "Data posted successfully!", { position: "top-center" });
            return response.data;
        } catch (error) {
            console.error("API Error:", error);
        } finally {
            setLoadingUpdateSal(false);
        }
    };

    const handleLogout = async () => {
        try {

            await fetch("http://localhost:8000/api/logout", {
                method: "POST",
                credentials: "include",
            });


            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/';
        } catch (err) {
            console.error("logout Failed: ", err);

            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/';
        }
    };

    return (
        <>
            <ToastContainer transition={Slide} closeButton={false} limit={3}>
            </ToastContainer>
            <div className="container">
                <div className="main-title">
                    <h2>User Management</h2>
                </div>
                <div className="logout-button" style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                        className="logout"
                        onClick={handleLogout}
                    >
                        Logout
                    </button>
                </div>
                <form onSubmit={editId ? updateUser : createUser}>
                    <input
                        type="text"
                        placeholder="Name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                    />
                    <input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                    <button type="submit" className="add-update-button" disabled={loading}>
                        {editId ? (
                            loadingUpdate ? <div className="spinner"></div> : "Update"
                        ) : (
                            loadingAdd ? <div className="spinner"></div> : "Add"
                        )}
                    </button>
                </form>
                <ul className="users-container">
                    <h2 style={{ display: "flex" }}>Users:</h2>
                    {Array.isArray(users) && users.length > 0 ? (
                        users.map((user) => (
                            <li key={user.id}>
                                <div className="users-list">
                                    <div className="list-body">
                                        <span style={{ width: "80px" }}>{user.name}</span>
                                        <span> ({user.email})</span>
                                    </div>
                                    <div className="buttons" style={{ display: "flex", flexDirection: "row", flexWrap: "wrap" }}>
                                        <button
                                            disabled={loading}
                                            style={{ width: "66.25px" }}
                                            onClick={() => {
                                                setEditId(user.id);
                                                setName(user.name);
                                                setEmail(user.email);
                                            }}
                                        >
                                            Edit
                                        </button>
                                        <button disabled={loading} onClick={() => {
                                            console.log("Attempting to delete user with ID:", user.id); // Debugging
                                            deleteUser(user.id);
                                        }}>
                                            Delete
                                        </button>
                                    </div>
                                </div>
                            </li>
                        ))
                    ) : (
                        <li>{loading ? <div className="loading-div"><span>Fetching users</span><div className="spinner"></div></div> : 'No users found.'}</li>
                    )}
                </ul>
                <h2><u>Postgre Functions</u></h2>
                <div className="sum-container">
                    <h3>Add Numbers</h3>
                    <input
                        type="number"
                        value={state.num1}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "num1", value: e.target.value })}
                        placeholder="Enter number 1"
                    />
                    <input
                        type="number"
                        value={state.num2}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "num2", value: e.target.value })}
                        placeholder="Enter number 2"
                    />
                    <button onClick={async () => {
                        console.log("Fetching sum for:", state.num1, state.num2);
                        if (!state.num1 || !state.num2) {
                            toast.warning("Both input fields are required!", { position: "top-center" });
                            return;
                        }
                        await postData("add_numbers", { a: state.num1, b: state.num2 }, "sumResult")
                    }}>
                        {loadingSum ? <div className="spinner"></div> : 'Get Sum'}
                    </button>
                    {state.sumResult && state.sumResult.sum !== undefined ? (
                        <p>Sum: {state.sumResult.sum}</p>
                    ) : (
                        <p>No result yet</p>
                    )}
                </div>
                <div className="container">
                    <h3>Calculate Square</h3>
                    <input
                        type="number"
                        value={state.squareNumber}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "squareNumber", value: e.target.value })}
                        placeholder="Enter a number"
                    />
                    <button disabled={loading} onClick={() => {
                        if (!state.squareNumber) {
                            toast.warning("Provide a valid input!", { position: "top-center" });
                            return;
                        }
                        fetchData(`square/${state.squareNumber}`, {}, "squareResult")
                    }}>
                        {loadingSquare ? <div className="spinner"></div> : 'Get Square'}
                    </button>
                    {state.squareResult && state.squareResult.square !== undefined ? (
                        <p>Square: {state.squareResult.square}</p>
                    ) : (
                        <p>No result yet</p>
                    )}
                </div>
                <div className="container">
                    <h3>Check Even or Odd</h3>
                    <input
                        type="number"
                        value={state.checkNumber}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "checkNumber", value: e.target.value })}
                        placeholder="Enter a number"
                    />
                    <button disabled={loading} onClick={() => {
                        if (!state.checkNumber) {
                            toast.warning("Provide a valid input!", { position: "top-center" });
                            return;
                        }
                        fetchData(`check_even_odd/${state.checkNumber}`, {}, "evenOddResult")
                    }}>
                        {loadingEvenOdd ? <div className="spinner"></div> : 'Check Number'}
                    </button>
                    {state.evenOddResult && state.evenOddResult.result !== undefined ? (
                        <p>The number is : {state.evenOddResult.result}</p>
                    ) : (
                        <p>No result yet</p>
                    )}
                </div>
                <div className="container">
                    <h3>Celsius to Farenheit</h3>
                    <input
                        type="number"
                        value={state.celsius}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "celsius", value: e.target.value })}
                        placeholder="Enter celsius value"
                    />
                    <button disabled={loading} onClick={async () => {
                        if (!state.celsius) {
                            toast.warning("Provide a valid input!", { position: "top-center" });
                            return;
                        }
                        await postData("celsius_to_fahrenheit", { celsius: state.celsius }, "farenheitResult")
                    }}>
                        {loadingTemperature ? <div className="spinner"></div> : 'Convert to Farenheit'}
                    </button>
                    {state.farenheitResult && state.farenheitResult.farenheit !== undefined ? (
                        <p>The converted result is : {state.farenheitResult.farenheit} ° F</p>
                    ) : (
                        <p>No result yet</p>
                    )}
                </div>
                <div className="container">
                    <h3>Find high salary employees</h3>
                    <input
                        type="number"
                        value={state.salaryThreshold}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "salaryThreshold", value: e.target.value })}
                        placeholder="Enter salary threshold"
                    />
                    <button disabled={loading} onClick={async () => {
                        setLoadingSalThres(true);
                        if (!state.salaryThreshold) {
                            toast.warning("Provide a valid input!", { position: "top-center" });
                            return;
                        }
                        try {
                            const response = await axios.get(`${API_URL}/high_salary_employees/${state.salaryThreshold}`);  //, {}, "highSalaryEmployees"
                            if (!response.data || response.data.length === 0) {
                                toast.info("No employees found with the given salary threshold.", { position: "top-center" });
                            } else {
                                dispatch({ type: "SET_RESULT", field: "highSalaryEmployees", value: response.data });
                            }
                        } catch (error) {
                            console.error("API Error:", error); // Log full error to check details
                            toast.error("Error fetching employees. Please try again.", { position: "top-center" });
                        } finally {
                            setLoadingSalThres(false);
                        }
                    }}>
                        {loadingSalThres ? <div className="spinner"></div> : 'Get result'}
                    </button>
                    <ul>
                        {Array.isArray(state.highSalaryEmployees) && state.highSalaryEmployees.length > 0 ? (
                            state.highSalaryEmployees.map((emp, index) => (
                                <li key={index}>{emp.emp_id} - {emp.emp_name} - {emp.emp_salary}</li>
                            ))
                        ) : (
                            <p>Enter threshold to find employees</p>
                        )}
                    </ul>
                </div>
                <div className="container">
                    <h3>Get employee salary using id</h3>
                    <input
                        type="number"
                        value={state.empId}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "empId", value: e.target.value })}
                        placeholder="Enter employee id"
                    />
                    <button disabled={loading} onClick={async () => {
                        if (!state.empId) {
                            toast.warning("Provide enter a valid employee id!", { position: "top-center" });
                            return;
                        }
                        const response = await fetchData(`get_employee_salary/${state.empId}`, {}, "employeeSalary");

                        if (!response || typeof response !== "object" || !("name" in response) || !("salary" in response)) {
                            toast.error("Employee not found!", { position: "top-center" });
                        }
                    }}>
                        {loadingSalary ? <div className="spinner"></div> : 'Get salary'}
                    </button>
                    <ul>
                        {state.employeeSalary ? (
                            typeof state.employeeSalary === "object" ? (
                                <li>{state.employeeSalary.name} - {state.employeeSalary.salary}</li>
                            ) : (
                                <p>No employee found</p>
                            )
                        ) : (
                            <p>Please enter an ID</p>
                        )}
                    </ul>
                </div>
                <div className="container">
                    <h3>Calculate bonus for employees using id</h3>
                    <input
                        type="number"
                        value={state.emp_id_bonus}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "emp_id_bonus", value: e.target.value })}
                        placeholder="Enter employee id"
                    />
                    <button disabled={loading} onClick={async () => {
                        if (!state.emp_id_bonus) {
                            toast.warning("Provide enter a valid employee id!", { position: "top-center" });
                            return;
                        }
                        const response = await fetchData(`calculate_bonus/${state.emp_id_bonus}`, {}, "bonus");

                        if (!response || typeof response !== "object" || !("name" in response) || !("bonus" in response)) {
                            toast.error("Employee not found!", { position: "top-center" });
                        }
                    }}>
                        {loadingBonus ? <div className="spinner"></div> : 'Get bonus (10% bonus)'}
                    </button>
                    <ul>
                        {state.bonus ? (
                            typeof state.bonus === "object" ? (
                                <li>{state.bonus.name} - {state.bonus.bonus}</li>
                            ) : (
                                <p>No employee found</p>
                            )
                        ) : (
                            <p>Please enter an ID</p>
                        )}
                    </ul>
                </div>
                <h2>
                    <u>Triggers</u>
                </h2>
                <div className="triggers-container">
                    <h3>Update Employee Salary</h3>
                    <input
                        type="number"
                        value={state.update_emp_id}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "update_emp_id", value: e.target.value })}
                        placeholder="Enter Employee ID"
                    />
                    <input
                        type="number"
                        value={state.newSalary}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "newSalary", value: e.target.value })}
                        placeholder="Enter new salary"
                    />
                    <button disabled={loading} onClick={async () => {
                        if (!state.update_emp_id || !state.newSalary) {
                            toast.warning("Please enter valid employee ID and new salary!", { position: "top-center" });
                            return;
                        }
                        await putData(`update_salary/${state.update_emp_id}`, { new_salary: parseInt(state.newSalary) }, "salaryUpdateResponse");
                    }}>
                        {loadingUpdateSal ? <div className="spinner"></div> : 'Update Salary'}
                    </button>
                    {state.salaryUpdateResponse !== null && <p>{state.salaryUpdateResponse.message}</p>}
                </div>
                {/* <div className="container">
          <h3>Salary Change Logs</h3>
          <button onClick={() => fetchData("get_salary_logs", {}, "salaryLogs")}>
            Fetch Logs
          </button>
          <ul>
            {state.salaryLogs.map((log, index) => (
              <li key={index}>{log.emp_id} - ${log.old_salary} → ${log.new_salary}</li>
            ))}
          </ul>
        </div> */}

                <SalaryLogsComponent state={state} dispatch={dispatch} API_URL={API_URL} />


                <h2><u>Procedures</u></h2>
                <div className="procedures-container">
                    <h3>Add employee using stored procedure</h3>
                    <input
                        type="text"
                        value={state.emp_name}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "emp_name", value: e.target.value })}
                        placeholder="Enter name"
                    />
                    <input
                        type="number"
                        value={state.emp_salary}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "emp_salary", value: e.target.value })}
                        placeholder="Enter salary"
                    />
                    <button disabled={loading} onClick={async () => {
                        if (!state.emp_name || !state.emp_salary) {
                            toast.warning("Name and salary fields cannot be empty!", { position: "top-center" });
                            return;
                        }
                        await postData("add_employee", { emp_name: state.emp_name, emp_salary: parseInt(state.emp_salary) }, "addEmployeeResponse")
                    }}>
                        {loadingAddEmp ? <div className="spinner"></div> : 'Add Employee'}
                    </button>
                    {state.addEmployeeResponse && state.addEmployeeResponse !== null && <p>{state.addEmployeeResponse.message}</p>}
                </div>
                <div className="container">
                    <h3>Increase employee salary % using stored procedure</h3>
                    <input
                        type="text"
                        value={state.salaryIncreasePercent}
                        onChange={(e) => dispatch({ type: "SET_INPUT", field: "salaryIncreasePercent", value: e.target.value })}
                        placeholder="Enter %"
                    />
                    <button disabled={loading} onClick={async () => {
                        if (!state.salaryIncreasePercent) {
                            toast.warning("Please enter valid percentage!", { position: "top-center" });
                            return;
                        }
                        await postData("increase_all_salaries", { increase_percent: parseInt(state.salaryIncreasePercent, 10) }, "salaryIncreasePercentResponse");
                    }}>
                        {loadingSalaryIncreasePercent ? <div className="spinner"></div> : 'Increase salary'}
                    </button>
                    {state.salaryIncreasePercentResponse && state.salaryIncreasePercentResponse !== null && <p>{state.salaryIncreasePercentResponse.message}</p>}
                </div>
            </div>
        </>
    );
}

export default Home;
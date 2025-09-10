import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [formData, setFormData] = useState({});
  const [responseData, setResponseData] = useState({});

  const handleSubmit = async (e) => {
      e.preventDefault();
      try {
          await axios.post('http://localhost:8084/api/v1/executions/webhook/company.team/webhook_example/abcdefg',
              formData).then(response => {
                setResponseData(response.data)
                
              }); 
      } catch (error) {
          console.error('Error:', error);
      }
  };

  const handleChange = (e) => {
      setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className='App'>
      <header className='App-header'>
        <h1>Kestra Webhook Example</h1>
        <p>Send a message to Kestra</p>
        <form onSubmit={handleSubmit}>
            <input type="text" name="dataField"
                onChange={handleChange} />
            <button type="submit">Submit</button>
        </form>
        {responseData.id && <p><b>Execution ID:</b> {responseData.id}</p>}
      </header>
    </div>
  );
}

export default App;

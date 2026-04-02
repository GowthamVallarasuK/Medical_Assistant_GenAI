// Simple test to check if AI services are running
const http = require('http');

const data = JSON.stringify({
  message: "I have fever and headache",
  session_id: "test_session",
  files: []
});

const options = {
  hostname: 'localhost',
  port: 8000,
  path: '/ai/diagnosis/process',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(data)
  }
};

const req = http.request(options, (res) => {
  console.log('📡 Sending request to AI services...');
  
  let responseData = '';
  
  res.on('data', (chunk) => {
    responseData += chunk;
  });
  
  res.on('end', () => {
    try {
      const result = JSON.parse(responseData);
      console.log('✅ Response received:', result);
      
      if (result.success) {
        console.log('🎉 AI Services Working!');
        console.log('📋 Primary Diagnosis:', result.diagnosis?.primary_condition);
        console.log('⚠️ Risk Level:', result.risk_level);
        console.log('💊 Response Length:', result.response?.length);
      } else {
        console.log('❌ Diagnosis failed');
        console.log('Error:', result);
      }
    } catch (error) {
      console.log('❌ Failed to parse response:', error);
    }
  });
});

req.on('error', (error) => {
  console.error('❌ Request failed:', error.message);
});

req.write(data);
req.end();

console.log('🧪 Testing AI diagnosis service...');
console.log('📡 Request data:', data);

// Test script to verify AI services are working
const axios = require('axios');

async function testDiagnosis() {
  try {
    console.log('🧪 Testing AI diagnosis service...');
    
    const response = await axios.post('http://localhost:8000/ai/diagnosis/process', {
      message: "I have fever and headache",
      session_id: "test_session",
      files: []
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('✅ Response:', response.data);
    
    if (response.data.success) {
      console.log('🎉 AI Services Working!');
      console.log('📋 Diagnosis:', response.data.diagnosis);
      console.log('⚠️ Risk Level:', response.data.risk_level);
      console.log('💊 Response:', response.data.response);
    } else {
      console.log('❌ Still failing');
    }
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

testDiagnosis();

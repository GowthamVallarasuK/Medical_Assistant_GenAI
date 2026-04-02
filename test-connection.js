// Test connection to AI services
const http = require('http');

function testConnection() {
  const options = {
    hostname: 'localhost',
    port: 8000,
    path: '/health',
    method: 'GET'
  };

  const req = http.request(options, (res) => {
    console.log('✅ AI Services Status:', res.statusCode);
    
    let data = '';
    res.on('data', (chunk) => {
      data += chunk;
    });
    
    res.on('end', () => {
      try {
        const result = JSON.parse(data);
        console.log('📊 Response:', result);
      } catch (e) {
        console.log('📊 Raw Response:', data);
      }
    });
  });

  req.on('error', (error) => {
    console.error('❌ Connection failed:', error.message);
    console.log('🔧 AI Services are NOT running');
    console.log('🚀 To start: cd ai-services && python start-ai-fixed.py');
  });

  req.end();
}

testConnection();

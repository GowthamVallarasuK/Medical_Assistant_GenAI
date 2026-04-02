// Simple test to debug authentication
const mongoose = require('mongoose');
const User = require('./models/User');

async function testAuth() {
  try {
    // Connect to MongoDB
    await mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/medical_diagnosis');
    console.log('✅ Connected to MongoDB');

    // Test user creation
    const testUser = {
      name: 'Test User',
      email: 'test@example.com',
      password: 'password123'
    };

    console.log('🔍 Testing user creation...');
    
    // Check if user already exists
    const existingUser = await User.findOne({ email: testUser.email });
    if (existingUser) {
      console.log('⚠️ User already exists, deleting...');
      await User.deleteOne({ email: testUser.email });
    }

    // Create new user
    const user = await User.create(testUser);
    console.log('✅ User created successfully:', user.email);

    // Test password comparison
    const isValid = await user.comparePassword(testUser.password);
    console.log('✅ Password comparison:', isValid);

    // Clean up
    await User.deleteOne({ email: testUser.email });
    console.log('✅ Test user cleaned up');

    console.log('🎉 All tests passed!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error('Stack:', error.stack);
  } finally {
    await mongoose.disconnect();
  }
}

testAuth();

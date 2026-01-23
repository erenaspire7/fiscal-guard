/**
 * Global test setup
 * Runs before all tests to seed demo data
 */

import { test as setup } from '@playwright/test';
import { seedDemoData } from '../utils/seed-data';

setup('seed demo data', async () => {
  console.log('\n🌱 Setting up test data...\n');
  await seedDemoData();
  console.log('✅ Test data ready\n');
});

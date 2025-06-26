// adaptive-bi-system/data_streaming/init-mongo.js
// This script runs when the MongoDB container starts for the first time
// It ensures the default database and user are set up.

print('Running init-mongo.js script...');

// Connect to the admin database to create root user
var adminDb = db.getSiblingDB('admin');

// Check if the user already exists to prevent errors on restart
if (adminDb.getUser('admin') == null) {
  print('Creating root user: admin');
  adminDb.createUser(
    {
      user: "admin",
      pwd: "admin123",
      roles: [ { role: "root", db: "admin" } ]
    }
  );
  print('Root user "admin" created.');
} else {
  print('Root user "admin" already exists. Skipping creation.');
}

// Ensure the application database exists and create collections if they don't
var appDb = db.getSiblingDB('adaptive_bi');

// Create collections if they don't exist
// MongoDB automatically creates collections on first insert, but explicitly creating
// can be good for schema validation or ensuring existence for tools.
var collections = ['users', 'products', 'transactions', 'feedback', 'user_activities'];

collections.forEach(function(collectionName) {
  if (!appDb.getCollectionNames().includes(collectionName)) {
    appDb.createCollection(collectionName);
    print('Collection "' + collectionName + '" created in "adaptive_bi" database.');
  } else {
    print('Collection "' + collectionName + '" already exists in "adaptive_bi" database.');
  }
});

print('init-mongo.js script finished.');
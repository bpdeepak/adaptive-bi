// adaptive-bi-system/backend/routes/users.js
const express = require('express');
const { getAllUsers, getUser, createUser, updateUser, deleteUser } = require('../controllers/userController');
const { protect, authorize } = require('../middleware/auth'); // Import auth middleware

const router = express.Router();

// Apply protection and authorization to all routes below this point
router.use(protect);
router.use(authorize('admin')); // Only 'admin' role can manage users

router.route('/')
  .get(getAllUsers)
  .post(createUser); // Admin can create users

router.route('/:id')
  .get(getUser)
  .put(updateUser)
  .delete(deleteUser);

module.exports = router;
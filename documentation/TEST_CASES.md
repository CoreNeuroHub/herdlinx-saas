# Test Cases for HerdLinx SaaS Application

This document contains comprehensive test cases for all user types in the HerdLinx cattle tracking SaaS application.

## Table of Contents

1. [Super Owner/Admin Test Cases](#1-super-owneradmin-test-cases)
2. [Business Owner/Admin Test Cases](#2-business-owneradmin-test-cases)
3. [User Test Cases](#3-user-test-cases)
4. [Cross-User Type Test Cases](#4-cross-user-type-test-cases)

---

## 1. Super Owner/Admin Test Cases

### 1.1 Authentication & Access

#### TC-SO-001: Login as Super Owner/Admin
**Objective:** Verify Super Owner/Admin can log in successfully

**Steps:**
1. Navigate to login page
2. Enter valid Super Owner/Admin username and password
3. Click "Login"

**Expected Result:**
- User is redirected to top-level dashboard
- Session is established with user_type = 'super_owner' or 'super_admin'
- Dashboard displays system-wide statistics

**Test Data:**
- Valid Super Owner/Admin credentials

---

#### TC-SO-002: Login with Invalid Credentials
**Objective:** Verify system rejects invalid login attempts

**Steps:**
1. Navigate to login page
2. Enter invalid username or password
3. Click "Login"

**Expected Result:**
- Error message: "Invalid username or password"
- User remains on login page
- No session is created

---

#### TC-SO-003: Access Dashboard
**Objective:** Verify Super Owner/Admin can access top-level dashboard

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to `/dashboard`

**Expected Result:**
- Dashboard loads successfully
- Displays aggregate statistics:
  - Total feedlots
  - Total pens
  - Total cattle
  - Total batches
  - Total users
- Shows recent feedlots (last 5)
- Dashboard widgets are customizable

---

#### TC-SO-004: Access Your Feedlots
**Objective:** Verify Super Owner/Admin can view all feedlots

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to `/feedlot-hub`

**Expected Result:**
- All feedlots in the system are displayed
- Each feedlot shows:
  - Name, location, feedlot code
  - Total pens count
  - Total cattle count
  - Owner information
- Search and filter functionality works
- Can navigate to individual feedlot views

---

### 1.2 Feedlot Management

#### TC-SO-005: Create New Feedlot
**Objective:** Verify Super Owner/Admin can create a new feedlot

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to dashboard
3. Click "Create Feedlot" button/modal
4. Fill in required fields:
   - Name: "Test Feedlot"
   - Location: "Test Location"
   - Feedlot Code: "TEST001"
   - Contact information (optional)
5. Submit form

**Expected Result:**
- Feedlot is created successfully
- Success message displayed
- Feedlot appears in your feedlots
- Feedlot code is unique and uppercase

**Test Data:**
- Name: "Test Feedlot"
- Location: "Test Location"
- Feedlot Code: "TEST001"
- Phone: "123-456-7890"
- Email: "test@example.com"
- Contact Person: "John Doe"

---

#### TC-SO-006: Create Feedlot with Duplicate Code
**Objective:** Verify system prevents duplicate feedlot codes

**Steps:**
1. Log in as Super Owner/Admin
2. Create a feedlot with code "TEST001"
3. Attempt to create another feedlot with code "TEST001"

**Expected Result:**
- Error message: "Feedlot code 'TEST001' already exists"
- Second feedlot is not created

---

#### TC-SO-007: View Feedlot Details
**Objective:** Verify Super Owner/Admin can view feedlot details

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to your feedlots
3. Click on a feedlot to view details

**Expected Result:**
- Feedlot details page loads
- Displays:
  - Feedlot name, location, code
  - Contact information
  - Statistics (pens, cattle, batches, users)
  - Owner information
  - Created date
- "Edit Feedlot" button is visible

---

#### TC-SO-008: Edit Feedlot
**Objective:** Verify Super Owner/Admin can edit feedlot information

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to a feedlot view page
3. Click "Edit Feedlot"
4. Modify feedlot details:
   - Change name
   - Update location
   - Change feedlot code
   - Update contact information
   - Assign/change owner
5. Save changes

**Expected Result:**
- Changes are saved successfully
- Success message displayed
- Updated information is reflected on feedlot view page
- Feedlot code uniqueness is validated if changed

**Test Data:**
- Updated Name: "Updated Feedlot Name"
- Updated Location: "Updated Location"
- Updated Feedlot Code: "TEST002"

---

#### TC-SO-009: Assign Business Owner to Feedlot
**Objective:** Verify Super Owner/Admin can assign a business owner to a feedlot

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to edit feedlot page
3. Select a business owner from dropdown
4. Save changes

**Expected Result:**
- Business owner is assigned to feedlot
- Owner information displays on feedlot view page
- Owner can now access the feedlot

---

### 1.3 User Management

#### TC-SO-010: View All Users
**Objective:** Verify Super Owner/Admin can view all system users

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to `/users` (Manage Users)

**Expected Result:**
- All users in the system are displayed
- User information includes:
  - Username, email
  - User type
  - Associated feedlots
  - Active/Inactive status
  - Created date
- Can filter/search users

---

#### TC-SO-011: Create Super Owner User
**Objective:** Verify Super Owner/Admin can create another Super Owner

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Manage Users
3. Click "Create User" or use registration modal
4. Fill in user details:
   - Username: "superowner2"
   - Email: "superowner2@example.com"
   - Password: "password123"
   - User Type: "Super Owner"
5. Submit

**Expected Result:**
- User is created successfully
- User type is set to 'super_owner'
- User can log in and access all system features
- No feedlot assignment required

---

#### TC-SO-012: Create Super Admin User
**Objective:** Verify Super Owner/Admin can create Super Admin users

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Manage Users
3. Create new user with type "Super Admin"

**Expected Result:**
- User is created successfully
- User type is set to 'super_admin'
- User has same permissions as Super Owner

---

#### TC-SO-013: Create Business Owner User
**Objective:** Verify Super Owner/Admin can create Business Owner users

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Manage Users
3. Create new user:
   - User Type: "Business Owner"
   - Assign one or more feedlots
4. Submit

**Expected Result:**
- User is created successfully
- User type is set to 'business_owner'
- User is assigned to selected feedlots
- User can access assigned feedlots only

---

#### TC-SO-014: Create Business Admin User
**Objective:** Verify Super Owner/Admin can create Business Admin users

**Steps:**
1. Log in as Super Owner/Admin
2. Create new user with type "Business Admin"
3. Assign feedlots

**Expected Result:**
- User is created successfully
- User type is set to 'business_admin'
- User can manage assigned feedlots

---

#### TC-SO-015: Create Regular User
**Objective:** Verify Super Owner/Admin can create regular users

**Steps:**
1. Log in as Super Owner/Admin
2. Create new user:
   - User Type: "User"
   - Assign single feedlot
4. Submit

**Expected Result:**
- User is created successfully
- User type is set to 'user'
- User is assigned to single feedlot
- User can only access assigned feedlot

---

#### TC-SO-016: Edit User Profile
**Objective:** Verify Super Owner/Admin can edit any user's profile

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Manage Users
3. Click "Edit" on a user
4. Modify user information:
   - Change username, email
   - Update user type
   - Change feedlot assignments
   - Update active status
   - Change password (optional)
5. Save changes

**Expected Result:**
- User information is updated successfully
- Changes are reflected immediately
- Username/email uniqueness is validated
- Feedlot assignments are updated correctly

---

#### TC-SO-017: Deactivate User
**Objective:** Verify Super Owner/Admin can deactivate users

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Manage Users
3. Click "Deactivate" on a user
4. Confirm deactivation

**Expected Result:**
- User is deactivated (is_active = False)
- User cannot log in
- Success message displayed
- Cannot deactivate own account

---

#### TC-SO-018: Activate User
**Objective:** Verify Super Owner/Admin can reactivate users

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Manage Users
3. Click "Activate" on an inactive user

**Expected Result:**
- User is activated (is_active = True)
- User can log in again
- Success message displayed

---

#### TC-SO-019: Prevent Self-Deactivation
**Objective:** Verify Super Owner/Admin cannot deactivate own account

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Manage Users
3. Attempt to deactivate own account

**Expected Result:**
- Error message: "You cannot deactivate your own account"
- Account remains active

---

### 1.4 Feedlot User Management

#### TC-SO-020: View Feedlot Users
**Objective:** Verify Super Owner/Admin can view users for a specific feedlot

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to a feedlot view page
3. Click "View Users" or navigate to `/feedlot/<feedlot_id>/users`

**Expected Result:**
- All users associated with the feedlot are displayed
- Includes:
  - Business owners/admins assigned to feedlot
  - Regular users assigned to feedlot
- Can create new users for the feedlot

---

#### TC-SO-021: Create User for Specific Feedlot
**Objective:** Verify Super Owner/Admin can create users for a specific feedlot

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to feedlot users page
3. Create new user with feedlot pre-selected

**Expected Result:**
- User is created with feedlot assignment
- User appears in feedlot users list
- User can access the assigned feedlot

---

### 1.5 API Key Management

#### TC-SO-022: Access API Keys Page
**Objective:** Verify Super Owner/Admin can access API keys management

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Settings → API Keys

**Expected Result:**
- API Keys page loads
- Lists all feedlots with their API keys
- Shows key status (active/inactive)
- Can generate, activate, deactivate, and delete keys

---

#### TC-SO-023: Generate API Key for Feedlot
**Objective:** Verify Super Owner/Admin can generate API keys

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to API Keys page
3. Select a feedlot
4. Click "Generate API Key"
5. Optionally add description
6. Confirm generation

**Expected Result:**
- API key is generated successfully
- Key is displayed (only once)
- Warning message about saving key
- Key is active by default
- Key appears in feedlot's API keys list

**Test Data:**
- Feedlot: Any existing feedlot
- Description: "Test API Key" (optional)

---

#### TC-SO-024: Deactivate API Key
**Objective:** Verify Super Owner/Admin can deactivate API keys

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to API Keys page
3. Find an active API key
4. Click "Deactivate"

**Expected Result:**
- API key is deactivated
- Key status changes to inactive
- API requests with this key will fail
- Success message displayed

---

#### TC-SO-025: Activate API Key
**Objective:** Verify Super Owner/Admin can reactivate API keys

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to API Keys page
3. Find an inactive API key
4. Click "Activate"

**Expected Result:**
- API key is activated
- Key status changes to active
- API requests with this key will succeed
- Success message displayed

---

#### TC-SO-026: Delete API Key
**Objective:** Verify Super Owner/Admin can delete API keys

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to API Keys page
3. Find an API key
4. Click "Delete"
5. Confirm deletion

**Expected Result:**
- API key is permanently deleted
- Key is removed from list
- API requests with this key will fail
- Success message displayed

---

### 1.6 Profile Management

#### TC-SO-027: View Own Profile
**Objective:** Verify Super Owner/Admin can view own profile

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Profile page

**Expected Result:**
- Profile page displays:
  - Username, email
  - First name, last name
  - Contact number
  - Profile picture
  - User type
- Can edit profile information

---

#### TC-SO-028: Update Own Profile
**Objective:** Verify Super Owner/Admin can update own profile

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Profile page
3. Update profile information:
   - Change first name, last name
   - Update contact number
   - Upload new profile picture
4. Save changes

**Expected Result:**
- Profile is updated successfully
- Changes are reflected immediately
- Session is updated with new profile data
- Success message displayed
- Profile picture upload works correctly
- File validation works (size, type)

---

#### TC-SO-029: Change Own Password
**Objective:** Verify Super Owner/Admin can change own password

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Profile page
3. Enter current password
4. Enter new password
5. Confirm new password
6. Save changes

**Expected Result:**
- Password is changed successfully
- Can log in with new password
- Cannot log in with old password
- Success message displayed

**Test Data:**
- Current Password: (existing password)
- New Password: "NewPassword123"
- Confirm Password: "NewPassword123"

---

#### TC-SO-030: Change Password with Wrong Current Password
**Objective:** Verify system validates current password

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Profile page
3. Enter incorrect current password
4. Enter new password
5. Attempt to save

**Expected Result:**
- Error message: "Current password is incorrect"
- Password is not changed

---

### 1.7 Dashboard Customization

#### TC-SO-031: Customize Dashboard Widgets
**Objective:** Verify Super Owner/Admin can customize dashboard layout

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to dashboard
3. Rearrange widgets (drag and drop)
4. Hide/show widgets
5. Resize widgets
6. Save preferences

**Expected Result:**
- Widget positions are saved
- Widget visibility is saved
- Widget sizes are saved
- Preferences persist across sessions

---

### 1.8 Access Control

#### TC-SO-032: Access Any Feedlot
**Objective:** Verify Super Owner/Admin can access any feedlot

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to your feedlots
3. Click on any feedlot
4. Access feedlot dashboard

**Expected Result:**
- Can access any feedlot regardless of ownership
- Can view all feedlot data
- Can manage feedlot resources

---

#### TC-SO-033: Access Feedlot Routes
**Objective:** Verify Super Owner/Admin can access all feedlot-level routes

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to any feedlot
3. Access:
   - Pens list
   - Batches list
   - Cattle list
   - Create/edit/delete operations
   - Manifest export

**Expected Result:**
- All feedlot routes are accessible
- Can perform all operations
- No access denied errors
- Can access manifest export functionality

---

#### TC-SO-035: Access Settings Page
**Objective:** Verify Super Owner/Admin can access settings page

**Steps:**
1. Log in as Super Owner/Admin
2. Navigate to Settings page

**Expected Result:**
- Settings page loads successfully
- Can access API Keys management
- Settings navigation works correctly

---

### 1.9 Logout

#### TC-SO-034: Logout
**Objective:** Verify Super Owner/Admin can log out

**Steps:**
1. Log in as Super Owner/Admin
2. Click logout button

**Expected Result:**
- Session is cleared
- User is redirected to login page
- Success message: "You have been logged out"
- Cannot access protected routes

---

## 2. Business Owner/Admin Test Cases

### 2.1 Authentication & Access

#### TC-BO-001: Login as Business Owner/Admin
**Objective:** Verify Business Owner/Admin can log in successfully

**Steps:**
1. Navigate to login page
2. Enter valid Business Owner/Admin credentials
3. Click "Login"

**Expected Result:**
- User is redirected to top-level dashboard
- Session is established with user_type = 'business_owner' or 'business_admin'
- Dashboard shows only assigned feedlots

**Test Data:**
- Valid Business Owner/Admin credentials

---

#### TC-BO-002: Access Dashboard (Filtered View)
**Objective:** Verify Business Owner/Admin sees only assigned feedlots

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to `/dashboard`

**Expected Result:**
- Dashboard loads successfully
- Statistics only include assigned feedlots
- Recent feedlots only show assigned feedlots
- Cannot see feedlots they're not assigned to

---

#### TC-BO-003: Access Your Feedlots (Filtered View)
**Objective:** Verify Business Owner/Admin sees only assigned feedlots

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to `/feedlot-hub`

**Expected Result:**
- Only assigned feedlots are displayed
- Cannot see other feedlots
- Can navigate to assigned feedlots

---

### 2.2 Feedlot Access Control

#### TC-BO-004: Access Assigned Feedlot
**Objective:** Verify Business Owner/Admin can access assigned feedlots

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to your feedlots
3. Click on an assigned feedlot

**Expected Result:**
- Feedlot dashboard loads successfully
- Can view feedlot details
- Can access all feedlot features

---

#### TC-BO-005: Cannot Access Unassigned Feedlot
**Objective:** Verify Business Owner/Admin cannot access unassigned feedlots

**Steps:**
1. Log in as Business Owner/Admin
2. Attempt to access a feedlot URL they're not assigned to
   - Direct URL: `/feedlot/<unassigned_feedlot_id>/dashboard`

**Expected Result:**
- Access denied error message
- Redirected to dashboard
- Cannot view feedlot data

---

#### TC-BO-006: Multiple Feedlot Access
**Objective:** Verify Business Owner/Admin with multiple feedlots can access all assigned feedlots

**Steps:**
1. Log in as Business Owner/Admin assigned to multiple feedlots
2. Navigate to your feedlots
3. Verify all assigned feedlots are visible
4. Access each assigned feedlot

**Expected Result:**
- All assigned feedlots are visible
- Can access all assigned feedlots
- Statistics aggregate across all assigned feedlots

---

### 2.3 User Management

#### TC-BO-007: View Feedlot Users
**Objective:** Verify Business Owner/Admin can view users for assigned feedlots

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to an assigned feedlot
3. Click "View Users" or navigate to feedlot users page

**Expected Result:**
- All users for the feedlot are displayed
- Can see:
  - Business owners/admins assigned to feedlot
  - Regular users assigned to feedlot

---

#### TC-BO-008: Create User for Assigned Feedlot
**Objective:** Verify Business Owner/Admin can create users for assigned feedlots

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to feedlot users page for an assigned feedlot
3. Create new user:
   - User Type: "User" or "Business Admin" or "Business Owner"
   - Assign to feedlot(s) they have access to
4. Submit

**Expected Result:**
- User is created successfully
- User is assigned to selected feedlot
- User appears in feedlot users list
- Cannot assign user to feedlots they don't have access to

---

#### TC-BO-009: Cannot Create Super Owner/Admin
**Objective:** Verify Business Owner/Admin cannot create Super Owner/Admin users

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to user creation
3. Attempt to select "Super Owner" or "Super Admin" as user type

**Expected Result:**
- Super Owner/Admin options are not available or disabled
- If attempted, error message: "Business owner and business admin cannot create super owner or super admin users"
- User is not created

---

#### TC-BO-010: Create User with Feedlot Restriction
**Objective:** Verify Business Owner/Admin can only assign users to their own feedlots

**Steps:**
1. Log in as Business Owner/Admin
2. Create a new user
3. Attempt to assign user to a feedlot they don't have access to

**Expected Result:**
- Error message: "You can only assign feedlots that you have access to"
- User is not created
- Only accessible feedlots are shown in selection

---

#### TC-BO-011: View All Users (Filtered)
**Objective:** Verify Business Owner/Admin can view users for their feedlots

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to `/users` (Manage Users)

**Expected Result:**
- Only users associated with assigned feedlots are displayed
- Cannot see users from other feedlots
- Can create users for assigned feedlots

---

### 2.4 Feedlot Management

#### TC-BO-012: View Feedlot Details
**Objective:** Verify Business Owner/Admin can view assigned feedlot details

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to an assigned feedlot
3. View feedlot details

**Expected Result:**
- Feedlot details page loads
- All feedlot information is visible
- Statistics are displayed
- Cannot edit feedlot (only Super Owner/Admin can edit)

---

#### TC-BO-013: Cannot Create Feedlot
**Objective:** Verify Business Owner/Admin cannot create new feedlots

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to dashboard
3. Look for "Create Feedlot" button

**Expected Result:**
- "Create Feedlot" button is not visible
- Cannot access feedlot creation route
- If attempted, access denied

---

#### TC-BO-014: Cannot Edit Feedlot
**Objective:** Verify Business Owner/Admin cannot edit feedlot information

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to an assigned feedlot view page
3. Look for "Edit Feedlot" button

**Expected Result:**
- "Edit Feedlot" button is not visible
- Cannot access feedlot edit route
- If attempted, access denied

---

### 2.5 Feedlot Operations

#### TC-BO-015: Access Feedlot Dashboard
**Objective:** Verify Business Owner/Admin can access feedlot dashboard

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to an assigned feedlot dashboard

**Expected Result:**
- Feedlot dashboard loads
- Shows feedlot statistics:
  - Total pens
  - Total cattle
  - Total batches
- Shows recent batches
- Can navigate to pens, batches, cattle

---

#### TC-BO-016: Manage Pens
**Objective:** Verify Business Owner/Admin can manage pens in assigned feedlots

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to pens list for an assigned feedlot
3. Create a new pen
4. Edit an existing pen
5. View pen details
6. Delete a pen

**Expected Result:**
- All pen operations work correctly
- Can create, edit, view, and delete pens
- Pen map functionality works

**Test Data:**
- Pen Number: "PEN-001"
- Capacity: 50
- Description: "Test Pen"

---

#### TC-BO-017: Manage Batches
**Objective:** Verify Business Owner/Admin can manage batches in assigned feedlots

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to batches list for an assigned feedlot
3. Create a new batch
4. View batch details

**Expected Result:**
- Can create batches
- Can view batch details
- Batch information is displayed correctly

**Test Data:**
- Batch Number: "BATCH-001"
- Induction Date: (current date)
- Funder: "Test Funder"
- Notes: "Test batch"

---

#### TC-BO-018: Manage Cattle
**Objective:** Verify Business Owner/Admin can manage cattle in assigned feedlots

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to cattle list for an assigned feedlot
3. Create new cattle record (including color, breed, brand info)
4. View cattle details
5. Move cattle between pens
6. Add weight records
7. Update tags

**Expected Result:**
- All cattle operations work correctly
- Can create, view, and update cattle records
- Cattle movement works
- Weight tracking works
- Tag management works
- Additional cattle fields (color, breed, brand info) are saved and displayed

**Test Data:**
- Cattle ID: "CATTLE-001"
- Sex: "Male"
- Weight: 500.0
- Cattle Status: "Healthy"
- LF Tag: "LF123456"
- UHF Tag: "UHF123456"
- Color: "Black"
- Breed: "Angus"
- Brand Drawings: "Circle"
- Brand Locations: "Left hip"
- Other Marks: "Ear tag"

---

#### TC-BO-019: Search and Filter Cattle
**Objective:** Verify Business Owner/Admin can search and filter cattle

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to cattle list
3. Use search functionality
4. Apply filters:
   - Cattle status
   - Sex
   - Pen
5. Sort by different fields

**Expected Result:**
- Search works correctly
- Filters apply correctly
- Sorting works
- Results update dynamically

---

### 2.6 API Key Management

#### TC-BO-020: Cannot Access API Keys
**Objective:** Verify Business Owner/Admin cannot access API keys management

**Steps:**
1. Log in as Business Owner/Admin
2. Attempt to navigate to Settings → API Keys

**Expected Result:**
- Access denied error message
- Redirected to dashboard
- API Keys page is not accessible

---

### 2.7 Profile Management

#### TC-BO-021: Update Own Profile
**Objective:** Verify Business Owner/Admin can update own profile

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to Profile page
3. Update profile information
4. Save changes

**Expected Result:**
- Profile is updated successfully
- Changes are reflected
- Success message displayed

---

#### TC-BO-022: Change Own Password
**Objective:** Verify Business Owner/Admin can change own password

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to Profile page
3. Change password
4. Save changes

**Expected Result:**
- Password is changed successfully
- Can log in with new password

---

#### TC-BO-024: Upload Profile Picture
**Objective:** Verify Business Owner/Admin can upload profile picture

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to Profile page
3. Upload profile picture
4. Save changes

**Expected Result:**
- Profile picture is uploaded successfully
- Picture is displayed on profile page
- Picture appears in navigation/user menu

---

#### TC-BO-025: Access Manifest Export
**Objective:** Verify Business Owner/Admin can access manifest export functionality

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to an assigned feedlot
3. Access manifest export page

**Expected Result:**
- Can access manifest export page
- Can create and manage manifest templates
- Can export manifests

---

### 2.8 Dashboard Customization

#### TC-BO-023: Customize Dashboard
**Objective:** Verify Business Owner/Admin can customize dashboard

**Steps:**
1. Log in as Business Owner/Admin
2. Navigate to dashboard
3. Customize widget layout
4. Save preferences

**Expected Result:**
- Dashboard preferences are saved
- Layout persists across sessions

---

## 3. User Test Cases

### 3.1 Authentication & Access

#### TC-U-001: Login as User
**Objective:** Verify regular user can log in successfully

**Steps:**
1. Navigate to login page
2. Enter valid user credentials
3. Click "Login"

**Expected Result:**
- User is redirected directly to assigned feedlot dashboard
- Session is established with user_type = 'user'
- Cannot access top-level dashboard

**Test Data:**
- Valid user credentials

---

#### TC-U-002: Direct Access to Assigned Feedlot
**Objective:** Verify user is redirected to assigned feedlot after login

**Steps:**
1. Log in as regular user
2. Observe redirect after login

**Expected Result:**
- Automatically redirected to `/feedlot/<feedlot_id>/dashboard`
- Top-level dashboard is not accessible

---

#### TC-U-003: Cannot Access Top-Level Dashboard
**Objective:** Verify regular user cannot access top-level dashboard

**Steps:**
1. Log in as regular user
2. Attempt to navigate to `/dashboard`

**Expected Result:**
- Access denied error message
- Redirected to feedlot dashboard
- Cannot view system-wide statistics

---

#### TC-U-004: Cannot Access Other Feedlots
**Objective:** Verify regular user cannot access other feedlots

**Steps:**
1. Log in as regular user
2. Attempt to access a different feedlot URL:
   - `/feedlot/<other_feedlot_id>/dashboard`

**Expected Result:**
- Access denied error message
- Redirected to assigned feedlot dashboard
- Cannot view other feedlot data

---

### 3.2 Feedlot Operations

#### TC-U-005: Access Feedlot Dashboard
**Objective:** Verify user can access assigned feedlot dashboard

**Steps:**
1. Log in as regular user
2. View feedlot dashboard

**Expected Result:**
- Feedlot dashboard loads
- Shows feedlot statistics
- Can navigate to pens, batches, cattle

---

#### TC-U-006: View Pens
**Objective:** Verify user can view pens in assigned feedlot

**Steps:**
1. Log in as regular user
2. Navigate to pens list

**Expected Result:**
- Pens list loads
- Shows all pens in feedlot
- Displays pen capacity and current count
- Can view pen details
- Can view pen map

---

#### TC-U-007: Create Pen
**Objective:** Verify user can create pens

**Steps:**
1. Log in as regular user
2. Navigate to pens list
3. Click "Create Pen"
4. Fill in pen details:
   - Pen Number: "PEN-001"
   - Capacity: 50
   - Description: "Test Pen"
5. Submit

**Expected Result:**
- Pen is created successfully
- Pen appears in pens list
- Success message displayed

**Test Data:**
- Pen Number: "PEN-001"
- Capacity: 50
- Description: "Test Pen"

---

#### TC-U-008: Edit Pen
**Objective:** Verify user can edit pens

**Steps:**
1. Log in as regular user
2. Navigate to pens list
3. Click on a pen to view details
4. Click "Edit Pen"
5. Modify pen information
6. Save changes

**Expected Result:**
- Pen is updated successfully
- Changes are reflected
- Success message displayed

---

#### TC-U-009: Delete Pen
**Objective:** Verify user can delete pens

**Steps:**
1. Log in as regular user
2. Navigate to pens list
3. Click "Delete" on a pen
4. Confirm deletion

**Expected Result:**
- Pen is deleted successfully
- Pen is removed from list
- Success message displayed

---

#### TC-U-010: View Pen Details
**Objective:** Verify user can view pen details

**Steps:**
1. Log in as regular user
2. Navigate to pens list
3. Click on a pen

**Expected Result:**
- Pen details page loads
- Shows:
  - Pen number, capacity, description
  - Current cattle count
  - List of cattle in pen
- Can view individual cattle records

---

#### TC-U-011: View Pen Map
**Objective:** Verify user can view pen map

**Steps:**
1. Log in as regular user
2. Navigate to pens list
3. Click "View Map" or navigate to pen map view

**Expected Result:**
- Pen map displays
- Shows pen layout
- Pens are positioned on grid
- Can view pen details from map

---

#### TC-U-012: Create Pen Map
**Objective:** Verify user can create/edit pen map

**Steps:**
1. Log in as regular user
2. Navigate to pen map creation page
3. Set grid dimensions
4. Place pens on grid
5. Save map

**Expected Result:**
- Pen map is saved successfully
- Map is displayed correctly
- Pens are positioned as placed

---

#### TC-U-013: View Batches
**Objective:** Verify user can view batches

**Steps:**
1. Log in as regular user
2. Navigate to batches list

**Expected Result:**
- Batches list loads
- Shows all batches in feedlot
- Displays batch number, induction date, cattle count
- Can view batch details

---

#### TC-U-014: Create Batch
**Objective:** Verify user can create batches

**Steps:**
1. Log in as regular user
2. Navigate to batches list
3. Click "Create Batch"
4. Fill in batch details:
   - Batch Number: "BATCH-001"
   - Induction Date: (current date)
   - Funder: "Test Funder"
   - Notes: "Test batch"
5. Submit

**Expected Result:**
- Batch is created successfully
- Batch appears in batches list
- Success message displayed

**Test Data:**
- Batch Number: "BATCH-001"
- Induction Date: (current date)
- Funder: "Test Funder"
- Notes: "Test batch"

---

#### TC-U-015: View Batch Details
**Objective:** Verify user can view batch details

**Steps:**
1. Log in as regular user
2. Navigate to batches list
3. Click on a batch

**Expected Result:**
- Batch details page loads
- Shows:
  - Batch number, induction date
  - Funder, notes
  - Cattle count
  - List of cattle in batch
- Can view individual cattle records

---

#### TC-U-016: View Cattle List
**Objective:** Verify user can view cattle list

**Steps:**
1. Log in as regular user
2. Navigate to cattle list

**Expected Result:**
- Cattle list loads
- Shows all cattle in feedlot
- Displays:
  - Cattle ID
  - Sex, weight, cattle status
  - Current pen
  - Tags (LF, UHF)
- Can search and filter

---

#### TC-U-017: Search Cattle
**Objective:** Verify user can search cattle

**Steps:**
1. Log in as regular user
2. Navigate to cattle list
3. Enter search term in search box
4. Submit search

**Expected Result:**
- Search results are displayed
- Results match search criteria
- Can search by cattle ID, tags

**Test Data:**
- Search Term: "CATTLE-001"

---

#### TC-U-018: Filter Cattle
**Objective:** Verify user can filter cattle

**Steps:**
1. Log in as regular user
2. Navigate to cattle list
3. Apply filters:
   - Cattle status: "Healthy"
   - Sex: "Male"
   - Pen: (select pen)
4. Apply filters

**Expected Result:**
- Filtered results are displayed
- Only matching cattle are shown
- Filters can be combined

---

#### TC-U-019: Sort Cattle
**Objective:** Verify user can sort cattle list

**Steps:**
1. Log in as regular user
2. Navigate to cattle list
3. Select sort field: "Weight"
4. Select sort order: "Descending"

**Expected Result:**
- Cattle list is sorted by weight (descending)
- Sort persists during session
- Can sort by different fields

---

#### TC-U-020: Create Cattle Record
**Objective:** Verify user can create cattle records

**Steps:**
1. Log in as regular user
2. Navigate to cattle list
3. Click "Create Cattle"
4. Fill in cattle details:
   - Batch: (select batch)
   - Cattle ID: "CATTLE-001"
   - Sex: "Male"
   - Weight: 500.0
   - Cattle Status: "Healthy"
   - LF Tag: "LF123456"
   - UHF Tag: "UHF123456"
   - Pen: (select pen or leave empty)
   - Color: "Black"
   - Breed: "Angus"
   - Brand Drawings: "Circle"
   - Brand Locations: "Left hip"
   - Other Marks: "Ear tag"
   - Notes: "Test cattle"
5. Submit

**Expected Result:**
- Cattle record is created successfully
- Cattle appears in cattle list
- Success message displayed
- Pen capacity is validated
- All additional fields (color, breed, brand info) are saved

**Test Data:**
- Batch: (existing batch)
- Cattle ID: "CATTLE-001"
- Sex: "Male"
- Weight: 500.0
- Cattle Status: "Healthy"
- LF Tag: "LF123456"
- UHF Tag: "UHF123456"
- Pen: (existing pen or None)
- Color: "Black"
- Breed: "Angus"
- Brand Drawings: "Circle"
- Brand Locations: "Left hip"
- Other Marks: "Ear tag"
- Notes: "Test cattle"

---

#### TC-U-021: Create Cattle with Full Pen
**Objective:** Verify system prevents creating cattle when pen is full

**Steps:**
1. Log in as regular user
2. Create a pen with capacity 1
3. Add one cattle to the pen
4. Attempt to create another cattle and assign to same pen

**Expected Result:**
- Error message: "Pen is at full capacity"
- Cattle is not created
- Must select different pen or leave pen empty

---

#### TC-U-022: View Cattle Details
**Objective:** Verify user can view cattle details

**Steps:**
1. Log in as regular user
2. Navigate to cattle list
3. Click on a cattle record

**Expected Result:**
- Cattle details page loads
- Shows:
  - Cattle ID, sex, weight
  - Cattle status
  - Current pen
  - Batch information
  - Tags (LF, UHF)
  - Color, breed
  - Brand drawings, brand locations
  - Other marks
  - Weight history
  - Tag history
  - Notes

---

#### TC-U-023: Move Cattle Between Pens
**Objective:** Verify user can move cattle between pens

**Steps:**
1. Log in as regular user
2. Navigate to a cattle record
3. Click "Move Cattle"
4. Select new pen
5. Submit

**Expected Result:**
- Cattle is moved successfully
- Old pen count decreases
- New pen count increases
- Movement is recorded
- Success message displayed

**Test Data:**
- New Pen: (select different pen with available capacity)

---

#### TC-U-024: Move Cattle to Full Pen
**Objective:** Verify system prevents moving cattle to full pen

**Steps:**
1. Log in as regular user
2. Create a pen with capacity 1
3. Add one cattle to the pen
4. Attempt to move another cattle to this pen

**Expected Result:**
- Error message: "Selected pen is at full capacity"
- Cattle is not moved
- Must select different pen

---

#### TC-U-025: Add Weight Record
**Objective:** Verify user can add weight records for cattle

**Steps:**
1. Log in as regular user
2. Navigate to a cattle record
3. Click "Add Weight"
4. Enter weight: 550.0
5. Submit

**Expected Result:**
- Weight record is added successfully
- Weight history is updated
- Current weight is updated
- Success message displayed

**Test Data:**
- Weight: 550.0
- Recorded By: (current user)

---

#### TC-U-026: Update Tags
**Objective:** Verify user can update/re-pair tags for cattle

**Steps:**
1. Log in as regular user
2. Navigate to a cattle record
3. Click "Update Tags"
4. Enter new LF Tag: "LF789012"
5. Enter new UHF Tag: "UHF789012"
6. Submit

**Expected Result:**
- Tags are updated successfully
- Previous tag pair is saved to history
- New tags are displayed
- Success message displayed

**Test Data:**
- New LF Tag: "LF789012"
- New UHF Tag: "UHF789012"

---

### 3.3 User Management Restrictions

#### TC-U-027: Cannot Access User Management
**Objective:** Verify regular user cannot access user management

**Steps:**
1. Log in as regular user
2. Attempt to navigate to `/users` or feedlot users page

**Expected Result:**
- Access denied error message
- Redirected to feedlot dashboard
- Cannot view or create users

---

#### TC-U-028: Cannot Create Users
**Objective:** Verify regular user cannot create users

**Steps:**
1. Log in as regular user
2. Attempt to access user registration route

**Expected Result:**
- Access denied error message
- Cannot create users

---

### 3.4 Profile Management

#### TC-U-029: View Own Profile
**Objective:** Verify user can view own profile

**Steps:**
1. Log in as regular user
2. Navigate to Profile page

**Expected Result:**
- Profile page displays user information
- Can edit profile
- Cannot change user type or feedlot assignment

---

#### TC-U-030: Update Own Profile
**Objective:** Verify user can update own profile

**Steps:**
1. Log in as regular user
2. Navigate to Profile page
3. Update profile information
4. Save changes

**Expected Result:**
- Profile is updated successfully
- Changes are reflected
- Success message displayed

---

#### TC-U-031: Change Own Password
**Objective:** Verify user can change own password

**Steps:**
1. Log in as regular user
2. Navigate to Profile page
3. Change password
4. Save changes

**Expected Result:**
- Password is changed successfully
- Can log in with new password

---

#### TC-U-035: Upload Profile Picture
**Objective:** Verify user can upload profile picture

**Steps:**
1. Log in as regular user
2. Navigate to Profile page
3. Click "Choose File" for profile picture
4. Select an image file (PNG, JPG, JPEG, GIF, or WEBP)
5. Upload file
6. Save changes

**Expected Result:**
- Profile picture is uploaded successfully
- Picture is displayed on profile page
- Picture appears in navigation/user menu
- Old picture is replaced if one existed
- File size validation works (max 5MB)
- File type validation works (only image formats)

**Test Data:**
- Image file: Valid image file (< 5MB, PNG/JPG/JPEG/GIF/WEBP format)

---

#### TC-U-036: Upload Invalid Profile Picture
**Objective:** Verify system rejects invalid profile picture uploads

**Steps:**
1. Log in as regular user
2. Navigate to Profile page
3. Attempt to upload:
   - Non-image file (e.g., .txt, .pdf)
   - Image file larger than 5MB

**Expected Result:**
- Error message displayed for invalid file type
- Error message displayed for file size exceeding limit
- Profile picture is not updated

---

### 3.5 Feedlot Management Restrictions

#### TC-U-032: Cannot View Your Feedlots
**Objective:** Verify regular user cannot access your feedlots

**Steps:**
1. Log in as regular user
2. Attempt to navigate to `/feedlot-hub`

**Expected Result:**
- Access denied error message
- Redirected to feedlot dashboard

---

#### TC-U-033: Cannot Edit Feedlot
**Objective:** Verify regular user cannot edit feedlot information

**Steps:**
1. Log in as regular user
2. Attempt to access feedlot edit route

**Expected Result:**
- Access denied error message
- Cannot edit feedlot

---

### 3.6 Manifest Export

#### TC-U-037: Access Manifest Export Page
**Objective:** Verify user can access manifest export page

**Steps:**
1. Log in as regular user
2. Navigate to manifest export page

**Expected Result:**
- Manifest export page loads
- Can select cattle by pen or manual selection
- Can select manifest template
- Can enter manual manifest data

---

#### TC-U-038: Export Manifest Using Template
**Objective:** Verify user can export manifest using a template

**Steps:**
1. Log in as regular user
2. Navigate to manifest export page
3. Select cattle (by pen or manually)
4. Select a manifest template
5. Choose export format (PDF, HTML, or both)
6. Submit export

**Expected Result:**
- Manifest is generated successfully
- PDF/HTML file is downloaded or displayed
- Template data is populated correctly
- Cattle information is included in manifest

**Test Data:**
- Template: Existing manifest template
- Export Format: PDF

---

#### TC-U-039: Export Manifest with Manual Entry
**Objective:** Verify user can export manifest with manual data entry

**Steps:**
1. Log in as regular user
2. Navigate to manifest export page
3. Select cattle
4. Choose "No Template - Enter Manually"
5. Fill in manifest information:
   - Owner details
   - Dealer details
   - Destination information
   - Transporter information
6. Choose export format
7. Submit export

**Expected Result:**
- Manifest is generated successfully
- Manual data is included in manifest
- PDF/HTML file is downloaded or displayed

---

#### TC-U-040: View Manifest Templates
**Objective:** Verify user can view manifest templates

**Steps:**
1. Log in as regular user
2. Navigate to manifest templates page

**Expected Result:**
- List of manifest templates is displayed
- Can see template name, default status
- Can create, edit, or delete templates

---

#### TC-U-041: Create Manifest Template
**Objective:** Verify user can create manifest template

**Steps:**
1. Log in as regular user
2. Navigate to manifest templates page
3. Click "Create Template"
4. Fill in template details:
   - Template name
   - Owner information
   - Dealer information
   - Default destination
   - Default transporter
   - Default purpose
5. Optionally mark as default template
6. Save template

**Expected Result:**
- Template is created successfully
- Template appears in templates list
- Template can be used for manifest export

**Test Data:**
- Template Name: "Standard Export Template"
- Owner Name: "Test Owner"
- Owner Phone: "123-456-7890"
- Owner Address: "123 Test St"

---

#### TC-U-042: Edit Manifest Template
**Objective:** Verify user can edit manifest template

**Steps:**
1. Log in as regular user
2. Navigate to manifest templates page
3. Click "Edit" on a template
4. Modify template information
5. Save changes

**Expected Result:**
- Template is updated successfully
- Changes are reflected in template
- Updated template can be used for export

---

#### TC-U-043: Delete Manifest Template
**Objective:** Verify user can delete manifest template

**Steps:**
1. Log in as regular user
2. Navigate to manifest templates page
3. Click "Delete" on a template
4. Confirm deletion

**Expected Result:**
- Template is deleted successfully
- Template is removed from list
- Cannot use deleted template for export

---

### 3.7 Logout

#### TC-U-034: Logout
**Objective:** Verify user can log out

**Steps:**
1. Log in as regular user
2. Click logout button

**Expected Result:**
- Session is cleared
- User is redirected to login page
- Success message displayed
- Cannot access protected routes

---

## 4. Cross-User Type Test Cases

### 4.1 Security & Access Control

#### TC-X-001: Session Management
**Objective:** Verify sessions are properly managed across user types

**Steps:**
1. Log in as any user type
2. Verify session data is set correctly
3. Log out
4. Verify session is cleared

**Expected Result:**
- Session contains correct user_type
- Session contains correct feedlot assignments
- Session is cleared on logout
- Cannot access protected routes after logout

---

#### TC-X-002: Access Control Enforcement
**Objective:** Verify access control is enforced for all routes

**Steps:**
1. Log in as different user types
2. Attempt to access routes they shouldn't have access to
3. Verify access is denied

**Expected Result:**
- Access denied errors are shown
- Users are redirected appropriately
- No unauthorized data is exposed

---

#### TC-X-003: Password Security
**Objective:** Verify password security across all user types

**Steps:**
1. Create users of different types
2. Verify passwords are hashed
3. Attempt to log in with incorrect passwords
4. Verify password change requires current password

**Expected Result:**
- Passwords are hashed (bcrypt)
- Incorrect passwords are rejected
- Password changes require current password validation

---

#### TC-X-004: Inactive User Login
**Objective:** Verify inactive users cannot log in

**Steps:**
1. Deactivate a user (as Super Owner/Admin)
2. Attempt to log in as that user

**Expected Result:**
- Error message: "Account is inactive"
- User cannot log in
- Session is not created

---

### 4.2 Data Isolation

#### TC-X-005: Multi-Tenant Data Isolation
**Objective:** Verify data is properly isolated between feedlots

**Steps:**
1. Log in as user from Feedlot A
2. View cattle, pens, batches
3. Log in as user from Feedlot B
4. Verify Feedlot B data is different

**Expected Result:**
- Users only see data from their assigned feedlot(s)
- No data leakage between feedlots
- Statistics are feedlot-specific

---

#### TC-X-006: Business Owner Multi-Feedlot Access
**Objective:** Verify Business Owner/Admin with multiple feedlots sees correct data

**Steps:**
1. Create Business Owner assigned to Feedlot A and Feedlot B
2. Log in as Business Owner
3. Verify dashboard shows aggregate statistics
4. Access each feedlot separately
5. Verify data is correct for each feedlot

**Expected Result:**
- Dashboard aggregates data from both feedlots
- Each feedlot shows only its own data
- Can switch between feedlots
- No data mixing

---

### 4.3 Error Handling

#### TC-X-007: Invalid Route Access
**Objective:** Verify system handles invalid route access gracefully

**Steps:**
1. Log in as any user type
2. Attempt to access non-existent routes
3. Attempt to access routes with invalid IDs

**Expected Result:**
- 404 errors for non-existent routes
- Error messages for invalid IDs
- User is redirected appropriately

---

#### TC-X-008: Form Validation
**Objective:** Verify form validation works across all user types

**Steps:**
1. Log in as different user types
2. Submit forms with invalid data:
   - Missing required fields
   - Invalid data types
   - Duplicate values
3. Verify validation errors

**Expected Result:**
- Validation errors are displayed
- Forms are not submitted with invalid data
- Error messages are clear and helpful

---

### 4.4 UI/UX

#### TC-X-009: Responsive Design
**Objective:** Verify responsive design works for all user types

**Steps:**
1. Log in as different user types
2. Test on different screen sizes:
   - Mobile (< 640px)
   - Tablet (640px - 1024px)
   - Desktop (> 1024px)
3. Verify layout adapts correctly

**Expected Result:**
- Layout is responsive
- All features are accessible on all screen sizes
- Navigation works on mobile
- Forms are usable on touch devices

---

#### TC-X-010: Navigation Consistency
**Objective:** Verify navigation is consistent across user types

**Steps:**
1. Log in as different user types
2. Navigate through the application
3. Verify navigation menus are appropriate

**Expected Result:**
- Navigation shows only accessible features
- Menu structure is consistent
- Breadcrumbs work correctly
- Back navigation works

---

### 4.5 API Endpoints

#### TC-X-011: API Key Authentication
**Objective:** Verify API endpoints require valid API key authentication

**Steps:**
1. Attempt to access API endpoint without API key
2. Attempt to access API endpoint with invalid API key
3. Attempt to access API endpoint with inactive API key
4. Access API endpoint with valid active API key

**Expected Result:**
- Requests without API key are rejected (401)
- Requests with invalid API key are rejected (401)
- Requests with inactive API key are rejected (401)
- Requests with valid active API key are accepted

**Test Data:**
- Valid API key (from API Keys management)
- Invalid API key: "invalid_key_12345"
- Inactive API key (deactivated key)

---

#### TC-X-012: Sync Batches API Endpoint
**Objective:** Verify batches can be synced via API

**Steps:**
1. Generate API key for a feedlot
2. Send POST request to `/api/v1/feedlot/batches`
3. Include valid API key in header
4. Send batch data in request body

**Expected Result:**
- Batches are created/updated successfully
- Response includes success status and record counts
- Errors are reported for invalid records
- Feedlot code validation works

**Test Data:**
- API Key: Valid API key
- Request Body:
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "name": "BATCH-001",
      "funder": "Test Funder",
      "notes": "Test batch",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

#### TC-X-013: Sync Induction Events API Endpoint
**Objective:** Verify induction events can be synced via API

**Steps:**
1. Send POST request to `/api/v1/feedlot/induction-events`
2. Include valid API key
3. Send induction event data

**Expected Result:**
- New cattle records are created
- Batch association works correctly
- Errors are reported for missing batches

**Test Data:**
- Request Body:
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "livestock_id": 123,
      "batch_id": 1,
      "batch_name": "BATCH-001",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

#### TC-X-014: Sync Pairing Events API Endpoint
**Objective:** Verify pairing events can be synced via API

**Steps:**
1. Send POST request to `/api/v1/feedlot/pairing-events`
2. Include valid API key
3. Send pairing event data

**Expected Result:**
- Tag pairs are updated successfully
- Weight records are added if provided
- Errors are reported for missing livestock

**Test Data:**
- Request Body:
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "livestock_id": 123,
      "lf_id": "LF123456",
      "epc": "UHF123456",
      "weight_kg": 500.0
    }
  ]
}
```

---

#### TC-X-015: Sync Checkin Events API Endpoint
**Objective:** Verify checkin events can be synced via API

**Steps:**
1. Send POST request to `/api/v1/feedlot/checkin-events`
2. Include valid API key
3. Send checkin event data with weight

**Expected Result:**
- Weight records are added successfully
- Errors are reported for missing livestock or invalid weight

**Test Data:**
- Request Body:
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "livestock_id": 123,
      "weight_kg": 550.0
    }
  ]
}
```

---

#### TC-X-016: Sync Repair Events API Endpoint
**Objective:** Verify repair events can be synced via API

**Steps:**
1. Send POST request to `/api/v1/feedlot/repair-events`
2. Include valid API key
3. Send repair event data

**Expected Result:**
- Tag pairs are updated successfully
- Repair reason is added to notes
- Errors are reported for missing livestock

**Test Data:**
- Request Body:
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "livestock_id": 123,
      "old_lf_id": "LF123456",
      "new_lf_id": "LF789012",
      "old_epc": "UHF123456",
      "new_epc": "UHF789012",
      "reason": "Tag damaged"
    }
  ]
}
```

---

#### TC-X-017: API Feedlot Code Validation
**Objective:** Verify API validates feedlot code matches API key

**Steps:**
1. Generate API key for Feedlot A
2. Send API request with Feedlot B's code
3. Send API request with correct feedlot code

**Expected Result:**
- Request with mismatched feedlot code is rejected (403)
- Request with correct feedlot code is accepted
- Error message indicates feedlot code mismatch

---

#### TC-X-018: API Error Handling
**Objective:** Verify API handles errors gracefully

**Steps:**
1. Send API requests with:
   - Missing required fields
   - Invalid data types
   - Malformed JSON
   - Empty data arrays

**Expected Result:**
- Appropriate error messages are returned
- HTTP status codes are correct (400, 401, 403, 500)
- Error details are included in response
- Partial success is reported when some records fail

---

## Test Execution Notes

### Prerequisites
- MongoDB database is set up and running
- Application is running
- Test users of each type are created
- Test feedlots are created
- Test data (pens, batches, cattle) is available

### Test Data Setup
Before executing test cases, ensure:
1. At least one Super Owner/Admin user exists
2. At least one Business Owner/Admin user exists (assigned to feedlots)
3. At least one regular User exists (assigned to a feedlot)
4. Multiple feedlots exist
5. Test feedlots have pens, batches, and cattle data

### Test Environment
- Use a dedicated test database
- Clear test data between test runs if needed
- Use unique test data to avoid conflicts

### Reporting
- Document test results (Pass/Fail)
- Note any bugs or issues found
- Include screenshots for visual issues
- Document steps to reproduce failures

---

## Test Case Status Legend

- **P** - Pass
- **F** - Fail
- **B** - Blocked
- **N/A** - Not Applicable
- **TBD** - To Be Determined

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-XX | Test Team | Initial test case document |
| 2.0 | 2024-12-XX | Test Team | Added manifest export test cases, API endpoint test cases, profile picture upload test cases, and updated cattle creation test cases with new fields |


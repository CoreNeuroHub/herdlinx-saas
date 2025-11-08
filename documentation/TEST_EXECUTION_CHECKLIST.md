# Test Execution Checklist

Quick reference checklist for executing test cases. Use this alongside the detailed test cases in `TEST_CASES.md`.

## Test Environment Setup

- [ ] MongoDB database is running
- [ ] Application server is running
- [ ] Test database is configured
- [ ] Test users are created:
  - [ ] Super Owner user
  - [ ] Super Admin user
  - [ ] Business Owner user (assigned to feedlots)
  - [ ] Business Admin user (assigned to feedlots)
  - [ ] Regular User (assigned to feedlot)
- [ ] Test feedlots are created
- [ ] Test data is available (pens, batches, cattle)

---

## 1. Super Owner/Admin Test Cases

### Authentication & Access
- [ ] TC-SO-001: Login as Super Owner/Admin
- [ ] TC-SO-002: Login with Invalid Credentials
- [ ] TC-SO-003: Access Dashboard
- [ ] TC-SO-004: Access Feedlot Hub

### Feedlot Management
- [ ] TC-SO-005: Create New Feedlot
- [ ] TC-SO-006: Create Feedlot with Duplicate Code
- [ ] TC-SO-007: View Feedlot Details
- [ ] TC-SO-008: Edit Feedlot
- [ ] TC-SO-009: Assign Business Owner to Feedlot

### User Management
- [ ] TC-SO-010: View All Users
- [ ] TC-SO-011: Create Super Owner User
- [ ] TC-SO-012: Create Super Admin User
- [ ] TC-SO-013: Create Business Owner User
- [ ] TC-SO-014: Create Business Admin User
- [ ] TC-SO-015: Create Regular User
- [ ] TC-SO-016: Edit User Profile
- [ ] TC-SO-017: Deactivate User
- [ ] TC-SO-018: Activate User
- [ ] TC-SO-019: Prevent Self-Deactivation

### Feedlot User Management
- [ ] TC-SO-020: View Feedlot Users
- [ ] TC-SO-021: Create User for Specific Feedlot

### API Key Management
- [ ] TC-SO-022: Access API Keys Page
- [ ] TC-SO-023: Generate API Key for Feedlot
- [ ] TC-SO-024: Deactivate API Key
- [ ] TC-SO-025: Activate API Key
- [ ] TC-SO-026: Delete API Key

### Profile Management
- [ ] TC-SO-027: View Own Profile
- [ ] TC-SO-028: Update Own Profile
- [ ] TC-SO-029: Change Own Password
- [ ] TC-SO-030: Change Password with Wrong Current Password

### Dashboard Customization
- [ ] TC-SO-031: Customize Dashboard Widgets

### Access Control
- [ ] TC-SO-032: Access Any Feedlot
- [ ] TC-SO-033: Access Feedlot Routes

### Logout
- [ ] TC-SO-034: Logout

---

## 2. Business Owner/Admin Test Cases

### Authentication & Access
- [ ] TC-BO-001: Login as Business Owner/Admin
- [ ] TC-BO-002: Access Dashboard (Filtered View)
- [ ] TC-BO-003: Access Feedlot Hub (Filtered View)

### Feedlot Access Control
- [ ] TC-BO-004: Access Assigned Feedlot
- [ ] TC-BO-005: Cannot Access Unassigned Feedlot
- [ ] TC-BO-006: Multiple Feedlot Access

### User Management
- [ ] TC-BO-007: View Feedlot Users
- [ ] TC-BO-008: Create User for Assigned Feedlot
- [ ] TC-BO-009: Cannot Create Super Owner/Admin
- [ ] TC-BO-010: Create User with Feedlot Restriction
- [ ] TC-BO-011: View All Users (Filtered)

### Feedlot Management
- [ ] TC-BO-012: View Feedlot Details
- [ ] TC-BO-013: Cannot Create Feedlot
- [ ] TC-BO-014: Cannot Edit Feedlot

### Feedlot Operations
- [ ] TC-BO-015: Access Feedlot Dashboard
- [ ] TC-BO-016: Manage Pens
- [ ] TC-BO-017: Manage Batches
- [ ] TC-BO-018: Manage Cattle
- [ ] TC-BO-019: Search and Filter Cattle

### API Key Management
- [ ] TC-BO-020: Cannot Access API Keys

### Profile Management
- [ ] TC-BO-021: Update Own Profile
- [ ] TC-BO-022: Change Own Password

### Dashboard Customization
- [ ] TC-BO-023: Customize Dashboard

---

## 3. User Test Cases

### Authentication & Access
- [ ] TC-U-001: Login as User
- [ ] TC-U-002: Direct Access to Assigned Feedlot
- [ ] TC-U-003: Cannot Access Top-Level Dashboard
- [ ] TC-U-004: Cannot Access Other Feedlots

### Feedlot Operations
- [ ] TC-U-005: Access Feedlot Dashboard
- [ ] TC-U-006: View Pens
- [ ] TC-U-007: Create Pen
- [ ] TC-U-008: Edit Pen
- [ ] TC-U-009: Delete Pen
- [ ] TC-U-010: View Pen Details
- [ ] TC-U-011: View Pen Map
- [ ] TC-U-012: Create Pen Map
- [ ] TC-U-013: View Batches
- [ ] TC-U-014: Create Batch
- [ ] TC-U-015: View Batch Details
- [ ] TC-U-016: View Cattle List
- [ ] TC-U-017: Search Cattle
- [ ] TC-U-018: Filter Cattle
- [ ] TC-U-019: Sort Cattle
- [ ] TC-U-020: Create Cattle Record
- [ ] TC-U-021: Create Cattle with Full Pen
- [ ] TC-U-022: View Cattle Details
- [ ] TC-U-023: Move Cattle Between Pens
- [ ] TC-U-024: Move Cattle to Full Pen
- [ ] TC-U-025: Add Weight Record
- [ ] TC-U-026: Update Tags

### User Management Restrictions
- [ ] TC-U-027: Cannot Access User Management
- [ ] TC-U-028: Cannot Create Users

### Profile Management
- [ ] TC-U-029: View Own Profile
- [ ] TC-U-030: Update Own Profile
- [ ] TC-U-031: Change Own Password

### Feedlot Management Restrictions
- [ ] TC-U-032: Cannot View Feedlot Hub
- [ ] TC-U-033: Cannot Edit Feedlot

### Logout
- [ ] TC-U-034: Logout

---

## 4. Cross-User Type Test Cases

### Security & Access Control
- [ ] TC-X-001: Session Management
- [ ] TC-X-002: Access Control Enforcement
- [ ] TC-X-003: Password Security
- [ ] TC-X-004: Inactive User Login

### Data Isolation
- [ ] TC-X-005: Multi-Tenant Data Isolation
- [ ] TC-X-006: Business Owner Multi-Feedlot Access

### Error Handling
- [ ] TC-X-007: Invalid Route Access
- [ ] TC-X-008: Form Validation

### UI/UX
- [ ] TC-X-009: Responsive Design
- [ ] TC-X-010: Navigation Consistency

---

## Test Results Summary

### Super Owner/Admin
- Total Test Cases: 34
- Passed: ___
- Failed: ___
- Blocked: ___
- Pass Rate: ___%

### Business Owner/Admin
- Total Test Cases: 23
- Passed: ___
- Failed: ___
- Blocked: ___
- Pass Rate: ___%

### User
- Total Test Cases: 34
- Passed: ___
- Failed: ___
- Blocked: ___
- Pass Rate: ___%

### Cross-User Type
- Total Test Cases: 10
- Passed: ___
- Failed: ___
- Blocked: ___
- Pass Rate: ___%

### Overall
- Total Test Cases: 101
- Passed: ___
- Failed: ___
- Blocked: ___
- Pass Rate: ___%

---

## Issues Found

### Critical Issues
1. 
2. 
3. 

### High Priority Issues
1. 
2. 
3. 

### Medium Priority Issues
1. 
2. 
3. 

### Low Priority Issues
1. 
2. 
3. 

---

## Notes

### Test Execution Date
- Start Date: ___
- End Date: ___
- Duration: ___ days

### Test Environment
- Application Version: ___
- Database Version: ___
- Browser(s) Tested: ___
- Operating System(s): ___

### Testers
- Tester Name: ___
- Date: ___

---

## Sign-off

- [ ] All critical test cases passed
- [ ] All high priority issues resolved
- [ ] Test documentation complete
- [ ] Ready for next phase

**Approved By:** _________________  
**Date:** _________________


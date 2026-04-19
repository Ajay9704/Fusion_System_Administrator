/**
 * Application-wide constants
 */

// User Types
export const USER_TYPES = {
  STUDENT: 'student',
  FACULTY: 'faculty',
  STAFF: 'staff',
};

// Programmes
export const PROGRAMMES = ['B.Tech', 'B.Des', 'M.Tech', 'M.Des', 'Ph.D'];

// Categories
export const CATEGORIES = ['GEN', 'OBC', 'SC', 'ST', 'EWS', 'GEN-EWS'];

// Gender Options - matching backend validation (M, F, O)
export const GENDER_OPTIONS = [
  { value: 'M', label: 'Male' },
  { value: 'F', label: 'Female' },
  { value: 'O', label: 'Other' },
];

// Programme-Department Mapping for Student Creation
// Defines which departments are valid for each programme
export const PROGRAMME_DEPARTMENT_MAPPING = {
  'B.Tech': [
    'CSE', 'ECE', 'ME', 'MT', 'SM',
    'Natural Science', 'Mechatronics', 'Design'
  ],
  'B.Des': [
    'Design'
  ],
  'M.Tech': [
    // Regular departments (also available for M.Tech)
    'CSE', 'ECE', 'ME', 'SM',
    // Specialized M.Tech departments
    'CSE M.Tech', 'ECE M.Tech', 'MT',
    'Mechatronics', 'Workshop', 'Design'
  ],
  'M.Des': [
    'Design'
  ],
  'Ph.D': [
    // Regular departments (also available for Ph.D)
    'CSE', 'ECE', 'ME', 'SM', 'Natural Science',
    // Specialized Ph.D departments
    'CSE Ph.D', 'ECE Ph.D', 'Design',
    'Mechatronics', 'Workshop'
  ]
};

// Role Eligibility Constraints
export const ROLE_ELIGIBILITY = {
  // Faculty-only roles (academic and leadership positions)
  faculty_only: [
    'Professor', 'Associate Professor', 'Assistant Professor',
    'HOD', 'Dean', 'Director',
    'Head of Department', 'Associate Dean', 'Assistant Dean',
    'Professor Emeritus', 'Visiting Professor',
    'Programme Coordinator', 'Dean Student Welfare'
  ],

  // Staff-only roles (administrative and support positions)
  staff_only: [
    'Registrar', 'Assistant Registrar', 'Deputy Registrar',
    'Section Officer', 'Assistant Section Officer',
    'Clerk', 'Assistant', 'Peon', 'Driver',
    'Placement Officer', 'Placement Coordinator', 'Training and Placement Officer',
    'Placement Cell In-charge', 'Training and Placement Cell In-charge'
  ],

  // Roles that can be assigned to both faculty and staff
  both: [
    'Warden', 'Assistant Warden',
    'Department Coordinator', 'Exam Coordinator',
    'Hostel Manager', 'Mess Manager'
  ],

  // Student-only roles
  student_only: [
    'Class Representative', 'Student Representative',
    'Hostel Monitor', 'Mess Committee Member',
    'Cultural Secretary', 'Sports Secretary'
  ]
};

// Conflicting Roles - roles that cannot be assigned together
export const CONFLICTING_ROLES = {
  // Top leadership conflicts
  'Director': ['Dean', 'HOD', 'Head of Department', 'Registrar'],
  'Dean': ['Director'],
  'Registrar': ['Director', 'Dean'],

  // Department leadership (Dean can be HOD)
  'HOD': ['Director', 'Registrar'],
  'Head of Department': ['Director', 'Registrar'],

  // Academic hierarchy conflicts
  'Professor': ['Associate Professor', 'Assistant Professor'],
  'Associate Professor': ['Professor', 'Assistant Professor'],
  'Professor Emeritus': ['Professor', 'Associate Professor', 'Assistant Professor'],

  // Administrative hierarchy conflicts
  'Registrar': ['Assistant Registrar', 'Deputy Registrar', 'Section Officer'],
  'Assistant Registrar': ['Deputy Registrar', 'Section Officer'],
  'Deputy Registrar': ['Registrar', 'Section Officer'],
  'Section Officer': ['Clerk', 'Assistant', 'Peon'],

  // Student conflicts (students cannot have professional roles)
  'Class Representative': ['HOD', 'Dean', 'Director', 'Coordinator', 'Professor', 'Registrar'],
  'Student Representative': ['HOD', 'Dean', 'Director', 'Coordinator', 'Professor', 'Registrar'],
  'Cultural Secretary': ['HOD', 'Dean', 'Director'],
  'Sports Secretary': ['HOD', 'Dean', 'Director'],

  // Staff cannot hold faculty academic roles
  'Placement Officer': ['HOD', 'Dean', 'Director', 'Professor', 'Associate Professor'],
  'Section Officer': ['HOD', 'Dean', 'Director', 'Professor'],
  'Clerk': ['HOD', 'Dean', 'Director', 'Professor', 'Placement Officer'],

  // Placement cell hierarchy
  'Placement Officer': ['Placement Coordinator'],
  'Placement Coordinator': ['Training and Placement Officer'],
  'Training and Placement Officer': ['Placement Cell In-charge']
};

// Title Options
export const TITLE_OPTIONS = ['Dr.', 'Mr.', 'Mrs.', 'Ms.'];

// Designation Types
export const DESIGNATION_TYPES = {
  FACULTY: 'faculty',
  STAFF: 'staff',
};

// Notification Positions
export const NOTIFICATION_POSITIONS = {
  TOP_CENTER: 'top-center',
  TOP_RIGHT: 'top-right',
  BOTTOM_RIGHT: 'bottom-right',
};

// File Upload
export const MAX_FILE_SIZE_MB = 5;
export const ALLOWED_FILE_TYPES = ['text/csv'];

// API Endpoints (for reference)
export const API_ENDPOINTS = {
  USERS: '/users',
  ROLES: '/roles',
  DEPARTMENTS: '/departments',
  BATCHES: '/batches',
  DESIGNATIONS: '/designations',
};

// Pagination
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
};

// Date Formats
export const DATE_FORMATS = {
  DISPLAY: 'DD MMMM YYYY',
  SHORT: 'DD MMM YYYY',
  INPUT: 'YYYY-MM-DD',
};

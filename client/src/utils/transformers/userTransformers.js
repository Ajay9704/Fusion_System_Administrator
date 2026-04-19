/**
 * User Data Transformers
 * Transforms user data from API format to frontend format and vice versa
 */

/**
 * Transform single user object from API response
 */
export const userTransformer = (userData) => {
  if (!userData) return null;

  return {
    id: userData.id,
    username: userData.username || userData.user?.username,
    email: userData.email,
    firstName: userData.first_name || userData.firstName,
    lastName: userData.last_name || userData.lastName,
    fullName: `${userData.first_name || ''} ${userData.last_name || ''}`.trim(),
    userType: userData.user_type || userData.userType,
    title: userData.title,
    sex: userData.sex,
    dateOfBirth: userData.date_of_birth || userData.dateOfBirth,
    address: userData.address,
    phoneNumber: userData.phone_no || userData.phoneNumber,
    profilePicture: userData.profile_picture || userData.profilePicture,
    aboutMe: userData.about_me || userData.aboutMe,
    department: userData.department
      ? {
          id: userData.department.id,
          name: userData.department.name,
        }
      : null,
    roles: userData.roles || [],
    status: userData.user_status || userData.status,
    dateJoined: userData.date_joined || userData.dateJoined,
    lastLogin: userData.last_login || userData.lastLogin,
    isActive: userData.is_active || userData.isActive,
    // Student-specific fields
    programme: userData.programme,
    batch: userData.batch,
    cpi: userData.cpi,
    category: userData.category,
    fatherName: userData.father_name,
    motherName: userData.mother_name,
    hallNo: userData.hall_no,
    roomNo: userData.room_no,
    specialization: userData.specialization,
    currentSemester: userData.curr_semester_no,
    // Metadata
    created: userData.date_modified || userData.created,
    modified: userData.modified,
  };
};

/**
 * Transform user list from API response
 */
export const userListTransformer = (usersData) => {
  if (!Array.isArray(usersData)) return [];

  return usersData.map(user => userTransformer(user));
};

/**
 * Transform user data for API request (create/update)
 */
export const userDataForApi = (formData) => {
  return {
    username: formData.username?.toUpperCase(),
    email: formData.email,
    first_name: formData.firstName,
    last_name: formData.lastName,
    password: formData.password,
    title: formData.title,
    sex: formData.sex,
    date_of_birth: formData.dateOfBirth,
    address: formData.address,
    phone_no: formData.phoneNumber,
    user_type: formData.userType,
    profile_picture: formData.profilePicture,
    about_me: formData.aboutMe,
    department: formData.department,
    // Student-specific fields
    programme: formData.programme,
    batch: formData.batch,
    category: formData.category,
    father_name: formData.fatherName,
    mother_name: formData.motherName,
    hall_no: formData.hallNo,
    room_no: formData.roomNo,
    specialization: formData.specialization,
    // Staff/Faculty specific fields
    designation: formData.designation,
    joining_date: formData.joiningDate,
  };
};

/**
 * Transform filter parameters for user listing
 */
export const userFilterTransformer = (filters) => {
  const transformedFilters = {};

  if (filters.userType) {
    transformedFilters.user_type = filters.userType;
  }

  if (filters.department) {
    transformedFilters.department = filters.department;
  }

  if (filters.batch) {
    transformedFilters.batch = filters.batch;
  }

  if (filters.programme) {
    transformedFilters.programme = filters.programme;
  }

  if (filters.isActive !== undefined) {
    transformedFilters.is_active = filters.isActive;
  }

  return transformedFilters;
};
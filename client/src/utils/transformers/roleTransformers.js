/**
 * Role Data Transformers
 * Transforms role data from API format to frontend format and vice versa
 */

/**
 * Transform single role object from API response
 */
export const roleTransformer = (roleData) => {
  if (!roleData) return null;

  return {
    id: roleData.id,
    name: roleData.name,
    fullName: roleData.full_name || roleData.fullName,
    type: roleData.type,
    category: roleData.category,
    basic: roleData.basic || false,
    isSingular: roleData.is_singular || roleData.isSingular || false,
    department: roleData.dept_if_not_basic || roleData.department
      ? {
          id: roleData.dept_if_not_basic?.id || roleData.department?.id,
          name: roleData.dept_if_not_basic?.name || roleData.department?.name,
        }
      : null,
    // Module access permissions
    moduleAccess: roleData.module_access || roleData.moduleAccess || null,
    // Metadata
    created: roleData.created,
    modified: roleData.modified,
  };
};

/**
 * Transform role list from API response
 */
export const roleListTransformer = (rolesData) => {
  if (!Array.isArray(rolesData)) {
    // Handle case where API returns paginated response
    if (rolesData?.results && Array.isArray(rolesData.results)) {
      return {
        roles: rolesData.results.map(role => roleTransformer(role)),
        pagination: {
          count: rolesData.count,
          next: rolesData.next,
          previous: rolesData.previous,
        },
      };
    }
    return [];
  }

  return rolesData.map(role => roleTransformer(role));
};

/**
 * Transform role data for API request (create/update)
 */
export const roleDataForApi = (formData) => {
  return {
    name: formData.name,
    full_name: formData.fullName,
    type: formData.type,
    category: formData.category,
    basic: formData.basic || false,
    is_singular: formData.isSingular || false,
    dept_if_not_basic: formData.department,
  };
};

/**
 * Transform module access data for API request
 */
export const moduleAccessDataForApi = (formData) => {
  return {
    designation: formData.designation,
    program_and_curriculum: formData.programAndCurriculum || false,
    course_registration: formData.courseRegistration || false,
    course_management: formData.courseManagement || false,
    other_academics: formData.otherAcademics || false,
    spacs: formData.spacs || false,
    department: formData.department || false,
    examinations: formData.examinations || false,
    hr: formData.hr || false,
    iwd: formData.iwd || false,
    complaint_management: formData.complaintManagement || false,
    fts: formData.fts || false,
    purchase_and_store: formData.purchaseAndStore || false,
    rspc: formData.rspc || false,
    hostel_management: formData.hostelManagement || false,
    mess_management: formData.messManagement || false,
    gymkhana: formData.gymkhana || false,
    placement_cell: formData.placementCell || false,
    visitor_hostel: formData.visitorHostel || false,
    phc: formData.phc || false,
    inventory_management: formData.inventoryManagement || false,
  };
};

/**
 * Transform user role assignment for API request
 */
export const userRoleAssignmentForApi = (username, roles) => {
  return {
    username: username,
    roles: roles.map(role => ({
      name: role.name || role,
      start_date: role.startDate,
      end_date: role.endDate,
    })),
  };
};
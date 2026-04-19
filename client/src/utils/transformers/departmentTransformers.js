/**
 * Department Data Transformers
 * Transforms department data from API format to frontend format and vice versa
 */

/**
 * Transform single department object from API response
 */
export const departmentTransformer = (departmentData) => {
  if (!departmentData) return null;

  return {
    id: departmentData.id,
    name: departmentData.name,
    parentDepartment: departmentData.parent_department
      ? {
          id: departmentData.parent_department.id,
          name: departmentData.parent_department.name,
        }
      : null,
    childDepartments: departmentData.child_departments
      ? departmentData.child_departments.map(child => ({
          id: child.id,
          name: child.name,
        }))
      : [],
    // Tree structure data
    level: departmentData.level || 0,
    path: departmentData.path || [],
    // Metadata
    created: departmentData.created,
    modified: departmentData.modified,
  };
};

/**
 * Transform department list from API response
 */
export const departmentListTransformer = (departmentsData) => {
  if (!Array.isArray(departmentsData)) {
    // Handle case where API returns paginated response
    if (departmentsData?.results && Array.isArray(departmentsData.results)) {
      return {
        departments: departmentsData.results.map(dept => departmentTransformer(dept)),
        pagination: {
          count: departmentsData.count,
          next: departmentsData.next,
          previous: departmentsData.previous,
        },
      };
    }
    return [];
  }

  return departmentsData.map(dept => departmentTransformer(dept));
};

/**
 * Transform department tree structure from API response
 */
export const departmentTreeTransformer = (treeData) => {
  if (!treeData) return null;

  const transformNode = (node) => {
    return {
      id: node.id,
      name: node.name,
      parent: node.parent,
      level: node.level || 0,
      children: node.children ? node.children.map(transformNode) : [],
    };
  };

  if (Array.isArray(treeData)) {
    return treeData.map(transformNode);
  }

  return transformNode(treeData);
};

/**
 * Transform department data for API request (create/update)
 */
export const departmentDataForApi = (formData) => {
  return {
    name: formData.name,
    parent_department: formData.parentDepartment || formData.parent_department,
  };
};
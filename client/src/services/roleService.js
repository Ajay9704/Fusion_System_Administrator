import apiClient from './api';

/**
 * Role Service - Handles all role-related API calls
 * Centralizes communication with backend role endpoints
 */

export const createCustomRole = async (roleData) => {
  const response = await apiClient.post('/create-role/', roleData);
  return response.data;
};

export const getAllRoles = async () => {
  const response = await apiClient.get('/view-roles/');
  return response.data;
};

export const getAllDesignations = async (designationType) => {
  const response = await apiClient.post('/view-designations/', designationType);
  return response.data;
};

export const getAllDepartments = async (type = 'staff') => {
  // type: 'student' or 'faculty' = academic only, 'staff' = all departments
  const academicOnly = type === 'student' || type === 'faculty';
  const response = await apiClient.get('/departments/', {
    params: { academic_only: academicOnly }
  });
  return response.data;
};

export const getAllBatches = async () => {
  const response = await apiClient.get('/batches/');
  return response.data;
};

export const getDepartmentsByProgramme = async (programme) => {
  const response = await apiClient.get('/departments/by-programme/', {
    params: { programme }
  });
  return response.data;
};

export const updateRole = async (roleId, roleData) => {
  const response = await apiClient.put(`/roles/${roleId}/`, roleData);
  return response.data;
};

export const deleteRole = async (roleId) => {
  const response = await apiClient.delete(`/roles/${roleId}/`);
  return response.data;
};

export const getRolePermissions = async (roleId) => {
  const response = await apiClient.get(`/roles/${roleId}/permissions/`);
  return response.data;
};

export const updateRolePermissions = async (roleId, permissions) => {
  const response = await apiClient.put(`/roles/${roleId}/permissions/`, permissions);
  return response.data;
};

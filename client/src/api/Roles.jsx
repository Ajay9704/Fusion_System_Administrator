import apiClient from '../services/api';

const API_URL = import.meta.env.VITE_BACKEND_URL + '/api';

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

export const getAllDepartments = async () => {
    const response = await apiClient.get('/departments/');
    return response.data;
};

export const getAllDepartmentsAdmin = async () => {
    const response = await apiClient.get('/departments/all/');
    return response.data;
};

export const getAllBatches = async () => {
    const response = await apiClient.get('/batches/');
    return response.data;
};
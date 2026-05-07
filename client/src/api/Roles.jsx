import apiClient from '../services/api';

export const createCustomRole = async (roleData) => {
    try {
        const response = await apiClient.post('/create-role/', roleData);
        return response.data;
    } catch (error) {
        console.error('Error creating custom role:', error.response?.data || error.message);
        throw error;
    }
};


export const getAllRoles = async () => {
    try {
        const response = await apiClient.get('/view-roles/');
        return response.data;
    } catch (error) {
        console.error('Error fetching roles:', error.response?.data || error.message);
        throw error;
    }
}

export const getAllDesignations = async (designationType) => {
    try {
        const response = await apiClient.post('/view-designations/', designationType);
        return response.data;
    } catch (error) {
        console.error('Error fetching designations:', error.response?.data || error.message);
        throw error;
    }
}

export const getAllDepartments = async (type = 'staff') => {
    try {
        // type: 'student' or 'faculty' = academic only, 'staff' = all departments
        const academicOnly = type === 'student' || type === 'faculty';
        const response = await apiClient.get('/departments/', {
            params: { academic_only: academicOnly }
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching departments:', error.response?.data || error.message);
        throw error;
    }
}

export const getAllBatches = async () => {
    try {
        const response = await apiClient.get('/batches/');
        return response.data;
    } catch (error) {
        console.error('Error fetching batches:', error.response?.data || error.message);
        throw error;
    }
}

export const getDepartmentsByProgramme = async (programme) => {
    try {
        const response = await apiClient.get('/departments/by-programme/', {
            params: { programme }
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching departments by programme:', error.response?.data || error.message);
        throw error;
    }
}

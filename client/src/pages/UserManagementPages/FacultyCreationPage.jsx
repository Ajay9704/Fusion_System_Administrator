import React, { useState, useEffect, useCallback } from 'react';
import {
    TextInput,
    Select,
    Button,
    Grid,
    Group,
    Box,
    Text,
    Title,
    Divider,
    Progress,
    Flex,
    Paper,
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { useMediaQuery } from '@mantine/hooks';
import { getAllDesignations, getAllDepartments } from '../../api/Roles';
import { createFaculty } from '../../api/Users';
import { formatDateForAPI } from '../../utils/dateUtils';
import { showErrorNotification, showSuccessNotification } from '../../utils/errorHandler';
import { GENDER_OPTIONS } from '../../utils/constants';

const REQUIRED_FIELDS = ['first_name', 'last_name', 'sex', 'designation', 'department', 'personal_email'];

const EMPTY_FORM = {
    username: '',
    first_name: '',
    last_name: '',
    department: '',
    title: '',
    designation: '',
    sex: '',
    dob: null,
    phone: '',
    address: '',
    personal_email: '',
};

const FacultyCreationPage = () => {
    const [formValues, setFormValues] = useState(EMPTY_FORM);
    const [departments, setDepartments] = useState([]);
    const [roles, setRoles] = useState([]);
    const [loading, setLoading] = useState(false);
    const matches = useMediaQuery('(min-width: 768px)');

    // Progress based only on required fields
    const progress = (REQUIRED_FIELDS.filter(f => formValues[f]).length / REQUIRED_FIELDS.length) * 100;

    const handleChange = (field, value) => {
        setFormValues(prev => ({ ...prev, [field]: value }));
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [deptRes, desigRes] = await Promise.all([
                    getAllDepartments(),
                    getAllDesignations({ category: 'faculty', basic: true }),
                ]);
                setDepartments(deptRes.map(d => ({ value: `${d.id}`, label: d.name })));
                setRoles(desigRes.map(d => ({ value: `${d.id}`, label: d.name })));
            } catch (error) {
                showErrorNotification(error, 'Load Error');
            }
        };
        fetchData();
    }, []);

    const handleSubmit = useCallback(async () => {
        if (!formValues.personal_email?.trim()) {
            showErrorNotification({ message: 'Personal email is required for credential delivery.' }, 'Validation Error');
            return;
        }
        try {
            setLoading(true);
            await createFaculty({
                ...formValues,
                dob: formatDateForAPI(formValues.dob),
            });
            showSuccessNotification('Faculty created successfully.');
            setFormValues(EMPTY_FORM);
        } catch (error) {
            showErrorNotification(error, 'Creation Error');
        } finally {
            setLoading(false);
        }
    }, [formValues]);

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Enter') { e.preventDefault(); handleSubmit(); }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleSubmit]);

    return (
        <Box maw={700} mx="auto" p="lg">
            <Paper shadow="xl" radius="lg" p="xl">
                <Flex justify="center" align="center" mb="md">
                    <Button
                        variant="gradient"
                        size="xl"
                        radius="xs"
                        gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
                        w={matches ? '500px' : '100%'}
                        style={{ fontSize: '1.8rem', lineHeight: 1.2 }}
                    >
                        <Title order={1} align="center" style={{ fontSize: '1.25rem', wordBreak: 'break-word' }}>
                            Add Faculty
                        </Title>
                    </Button>
                </Flex>

                <Divider my="sm" />
                <Progress value={progress} color="blue" mb="md" />

                <Grid gutter="md">
                    <Grid.Col span={12}>
                        <TextInput
                            label="Username"
                            placeholder="Leave blank to auto-generate"
                            description="Optional — auto-generated from first/last name if blank."
                            value={formValues.username}
                            onChange={(e) => handleChange('username', e.target.value)}
                        />
                    </Grid.Col>

                    <Grid.Col span={6}>
                        <TextInput
                            label="First Name"
                            placeholder="Enter first name"
                            value={formValues.first_name}
                            onChange={(e) => handleChange('first_name', e.target.value)}
                            required
                        />
                    </Grid.Col>

                    <Grid.Col span={6}>
                        <TextInput
                            label="Last Name"
                            placeholder="Enter last name"
                            value={formValues.last_name}
                            onChange={(e) => handleChange('last_name', e.target.value)}
                            required
                        />
                    </Grid.Col>

                    <Grid.Col span={6}>
                        <Select
                            label="Title"
                            placeholder="Select title"
                            data={['Dr.', 'Mr.', 'Mrs.', 'Ms.']}
                            value={formValues.title || null}
                            onChange={(value) => handleChange('title', value)}
                        />
                    </Grid.Col>

                    <Grid.Col span={6}>
                        <Select
                            label="Designation"
                            placeholder="Select designation"
                            data={roles}
                            value={formValues.designation ? `${formValues.designation}` : null}
                            onChange={(value) => handleChange('designation', value)}
                            required
                            searchable
                        />
                    </Grid.Col>

                    <Grid.Col span={12}>
                        <Select
                            label="Department"
                            placeholder="Select department"
                            data={departments}
                            value={formValues.department ? `${formValues.department}` : null}
                            onChange={(value) => handleChange('department', value)}
                            required
                            searchable
                        />
                    </Grid.Col>

                    <Grid.Col span={12}>
                        <Text fw={500} size="sm">Gender *</Text>
                        <Group spacing="sm" mt="xs">
                            {GENDER_OPTIONS.map((option) => (
                                <Button
                                    key={option.value}
                                    variant={formValues.sex === option.value ? 'filled' : 'light'}
                                    color={formValues.sex === option.value ? 'blue' : 'gray'}
                                    onClick={() => handleChange('sex', option.value)}
                                    size="sm"
                                    style={{
                                        flex: 1,
                                        transition: 'all 0.2s',
                                    }}
                                >
                                    {option.label}
                                </Button>
                            ))}
                        </Group>
                    </Grid.Col>

                    <Grid.Col span={6}>
                        <DateInput
                            label="Date of Birth"
                            placeholder="Pick a date"
                            value={formValues.dob}
                            onChange={(value) => handleChange('dob', value)}
                        />
                    </Grid.Col>

                    <Grid.Col span={6}>
                        <TextInput
                            label="Phone Number"
                            placeholder="Enter phone number"
                            value={formValues.phone}
                            onChange={(e) => handleChange('phone', e.target.value)}
                        />
                    </Grid.Col>

                    <Grid.Col span={12}>
                        <TextInput
                            label="Address"
                            placeholder="Enter address"
                            value={formValues.address}
                            onChange={(e) => handleChange('address', e.target.value)}
                        />
                    </Grid.Col>

                    <Grid.Col span={12}>
                        <TextInput
                            label="Personal / Alternate Email"
                            placeholder="Enter email for credential delivery"
                            value={formValues.personal_email}
                            onChange={(e) => handleChange('personal_email', e.target.value)}
                            required
                        />
                    </Grid.Col>
                </Grid>

                <Flex justify="center" mt="xl">
                    <Button onClick={handleSubmit} color="blue" size="md" loading={loading} fullWidth>
                        Add Faculty
                    </Button>
                </Flex>
            </Paper>
        </Box>
    );
};

export default FacultyCreationPage;

import React, { useState, useEffect } from 'react';
import {
    TextInput,
    Select,
    Button,
    Grid,
    Group,
    Box,
    NumberInput,
    Radio,
    rem,
    Title,
    Divider,
    Progress,
    Flex,
    Paper,
} from '@mantine/core';
import { FaCheck, FaTimes } from 'react-icons/fa';
import { notifications, showNotification } from '@mantine/notifications';
import { DateInput } from '@mantine/dates';
import { useMediaQuery } from "@mantine/hooks";
import { getAllDesignations, getAllDepartments } from '../../services/roleService';
import { createFaculty } from '../../services/userService';

const FacultyCreationPage = () => {
    const xIcon = <FaTimes style={{ width: rem(20), height: rem(20) }} />;
    const checkIcon = <FaCheck style={{ width: rem(20), height: rem(20) }} />;

    const [formValues, setFormValues] = useState({
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
    });

    const [progress, setProgress] = useState(0);
    const [roles, setRoles] = useState([]);
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');

    useEffect(() => {
        const totalFields = Object.keys(formValues).length;
        const filledFields = Object.values(formValues).filter((value) => value).length;
        setProgress((filledFields / totalFields) * 100);
    }, [formValues]);

    const handleChange = (field, value) => {
        setFormValues((prev) => ({ ...prev, [field]: value }));
        setErrorMessage('');
    };

    const fetchFacultyDesignations = async () => {
        try {
            let all_designations = [];
            const designationData = {
                category: 'faculty',
                basic: true,
            }
            const response = await getAllDesignations(designationData);
            console.log(response)
            for(let i=0; i<response.length; i++){
                all_designations[i] = {value: `${response[i].id}`, label: response[i].name}
            }
            setRoles(all_designations);
        } catch (error) {
            showNotification({
                title: 'Error',
                icon: xIcon,
                position: "top-center",
                withCloseButton: true,
                message: 'An error occurred while fetching designations.',
                color: 'red',
            });
        }
    }

    const fetchDepartments = async () => {
        try {
            let all_departments = [];
            const response = await getAllDepartments('faculty');
            console.log(response)
            for(let i=0; i<response.length; i++){
                all_departments[i] = {value: `${response[i].id}`, label: response[i].name}
            }
            setDepartments(all_departments);
        } catch (error) {
            showNotification({
                title: 'Error',
                icon: xIcon,
                position: "top-center",
                withCloseButton: true,
                message: 'An error occurred while fetching departments.',
                color: 'red',
            });
        }
    }

    const handleSubmit = async () => {
        try {
            setLoading(true);

            // ✅ CHANGE MADE: Format dob to "YYYY-MM-DD" string before sending to API
            const formattedFormValues = {
                ...formValues,
                dob: formValues.dob ? formValues.dob.toISOString().split('T')[0] : null,
            };

            const response = await createFaculty(formattedFormValues);

            showNotification({
                icon: checkIcon,
                title: "Faculty Created",
                position: "top-center",
                withCloseButton: true,
                autoClose: 5000,
                message: `Faculty member created successfully. Credentials sent to ${formValues.personal_email}`,
                color: "green",
            });
            console.log('Form Submitted', formValues);
            setFormValues({
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
            });
        } catch(error){
            console.error('Faculty creation error:', error);
            const errorMessage = error.response?.data
                ? (error.response.data.error?.message || error.response.data.message || JSON.stringify(error.response.data))
                : error.message;

            showNotification({
                title: 'Error Creating Faculty',
                icon: xIcon,
                position: "top-center",
                withCloseButton: true,
                autoClose: 8000,
                message: errorMessage || 'An error occurred while creating faculty.',
                color: 'red',
            });
        } finally {
            setLoading(false);
        }
    };

    useEffect(()=>{
        fetchFacultyDesignations();
        fetchDepartments();
    },[])

    useEffect(() => {
        const handleKeyDown = (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                handleSubmit();
            }
        };

        window.addEventListener('keydown', handleKeyDown);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [formValues]);

    const matches = useMediaQuery('(min-width: 768px)');

    return (
        <Box maw={700} mx="auto" p="lg">
            <Paper shadow="xl" radius="lg" p="xl">
                <Flex
                    gap="md"
                    justify="center"
                    align="center"
                    direction="row"
                    wrap="wrap"
                >

                    <Button
                        variant="gradient"
                        size="xl"
                        radius="xs"
                        gradient={{ from: "blue", to: "cyan", deg: 90 }}
                        w={matches && "500px"}
                        style={{
                            fontSize: "1.8rem",
                            lineHeight: 1.2,
                            marginBottom: "1rem",
                        }}
                    >
                        <Title
                            order={1}
                            align="center"
                            style={{
                                fontSize: "1.25rem",
                                wordBreak: "break-word",
                            }}
                        >
                            Add Faculty
                        </Title>
                    </Button>
                </Flex>

                <Divider my="sm" />

                {/* Progress Bar */}
                <Progress value={progress} color="blue" mb="md" />

                <Grid gutter="md">
                    {/* Personal Email - Required */}
                    <Grid.Col span={12}>
                        <TextInput
                            label="Personal Email"
                            placeholder="faculty.email@gmail.com"
                            value={formValues.personal_email}
                            onChange={(e) => handleChange('personal_email', e.target.value)}
                            required
                            description="Login credentials will be sent to this email"
                        />
                    </Grid.Col>

                    {/* Username - Optional */}
                    <Grid.Col span={12}>
                        <TextInput
                            label="Username (Optional)"
                            placeholder="Leave blank for auto-generation"
                            value={formValues.username}
                            onChange={(e) => handleChange('username', e.target.value)}
                            description="Auto-generated from name (e.g., snsharma)"
                        />
                    </Grid.Col>
                    {/* First Name */}
                    <Grid.Col span={6}>
                        <TextInput
                            label="First Name"
                            placeholder="Enter first name"
                            value={formValues.first_name}
                            onChange={(e) => handleChange('first_name', e.target.value)}
                            required
                        />
                    </Grid.Col>

                    {/* Last Name */}
                    <Grid.Col span={6}>
                        <TextInput
                            label="Last Name"
                            placeholder="Enter last name"
                            value={formValues.last_name}
                            onChange={(e) => handleChange('last_name', e.target.value)}
                            required
                        />
                    </Grid.Col>

                    {/* Department - MANDATORY for Faculty */}
                    <Grid.Col span={12}>
                        <Select
                            label="Department"
                            placeholder="Select department"
                            data={departments}
                            value={`${formValues.department}`}
                            onChange={(value) => handleChange('department', Number(value))}
                            required
                            description="Faculty must be assigned to a department"
                        />
                    </Grid.Col>

                    {/* Title */}
                    <Grid.Col span={6}>
                        <Select
                            label="Title"
                            placeholder="Select title"
                            data={['Dr.', 'Mr.', 'Mrs.', 'Ms.']}
                            value={formValues.title}
                            onChange={(value) => handleChange('title', value)}
                        />
                    </Grid.Col>

                    {/* Designation */}
                    <Grid.Col span={6}>
                        <Select
                            label="Designation"
                            placeholder="Select designation"
                            data={roles}
                            value={`${formValues.designation}`}
                            onChange={(value) => handleChange('designation', Number(value))}
                            required
                        />
                    </Grid.Col>

                    {/* Gender */}
                    <Grid.Col span={12}>
                        <Radio.Group
                            label="Gender"
                            value={formValues.sex}
                            onChange={(value) => handleChange('sex', value)}
                            required
                            styles={{
                                label: { marginRight: '1rem' },
                            }}
                        >
                            <Group spacing="sm" position="apart" mt="xs">
                                <Radio value="male" label="Male" />
                                <Radio value="female" label="Female" />
                                {/* <Radio value="other" label="Other" /> */}
                            </Group>
                        </Radio.Group>
                    </Grid.Col>

                    {/* Date of Birth */}
                    <Grid.Col span={6}>
                        <DateInput
                            value={formValues.dob}
                            onChange={(value) => handleChange('dob', value)}
                            label="Date of Birth"
                            placeholder="Pick a date"
                        />
                    </Grid.Col>

                    {/* Phone Number */}
                    <Grid.Col span={6}>
                        <NumberInput
                            label="Phone Number"
                            placeholder="Enter phone number"
                            value={formValues.phone}
                            onChange={(value) => handleChange('phone', value)}
                            hideControls
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
                </Grid>

                {/* Create Button */}
                <Flex
                    gap="md"
                    justify="center"
                    align="center"
                    direction="row"
                    wrap="wrap"
                    mt="xl"
                >
                    <Button onClick={handleSubmit} color="blue" size="md">
                        Add Faculty
                    </Button>
                </Flex>
            </Paper>
        </Box>
    );
};

export default FacultyCreationPage;

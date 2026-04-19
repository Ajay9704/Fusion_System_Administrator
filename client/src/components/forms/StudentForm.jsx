import React, { useState, useEffect, useMemo } from 'react';
import {
  TextInput,
  Select,
  Grid,
  Radio,
  FileInput,
  Progress,
  Button,
  Divider,
  Stack,
  Title,
  Group,
  Text,
  Alert,
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { FaDiceD6 } from 'react-icons/fa';
import {
  TITLE_OPTIONS,
  PROGRAMMES,
  CATEGORIES,
  GENDER_OPTIONS,
  PROGRAMME_DEPARTMENT_MAPPING
} from '../../utils/constants';

const StudentForm = ({ 
  initialValues, 
  onSubmit, 
  departments, 
  batches,
  onDownloadSampleCSV,
  onProgrammeChange,
  loading = false 
}) => {
  const [formValues, setFormValues] = useState(initialValues);
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    setFormValues(initialValues);
  }, [initialValues]);

  useEffect(() => {
    const totalFields = Object.keys(formValues).length;
    const filledFields = Object.values(formValues).filter((value) => value).length;
    setProgress((filledFields / totalFields) * 100);
  }, [formValues]);

  const handleChange = (field, value) => {
    // Special handling for programme change to enforce department constraints
    if (field === 'programme') {
      // Check if current department is valid for the new programme
      if (formValues.department) {
        const validDepartments = PROGRAMME_DEPARTMENT_MAPPING[value] || [];
        const currentDepartment = departments.find(d => String(d.value) === String(formValues.department));

        if (currentDepartment && !validDepartments.includes(currentDepartment.label)) {
          // Reset department if it's not valid for the new programme
          setFormValues((prev) => ({
            ...prev,
            [field]: value,
            department: '',
          }));
          return;
        }
      }
    }

    setFormValues((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Filter departments based on selected programme
  const availableDepartments = useMemo(() => {
    if (!formValues.programme) {
      return departments;
    }

    const validDepartments = PROGRAMME_DEPARTMENT_MAPPING[formValues.programme] || [];

    // More robust filtering - check for partial matches and case-insensitive comparison
    const filtered = departments.filter(dept => {
      const label = dept.label.trim();
      // Try exact match first
      if (validDepartments.includes(label)) {
        return true;
      }
      // Try case-insensitive match
      if (validDepartments.some(valid => valid.toLowerCase() === label.toLowerCase())) {
        return true;
      }
      // Try partial match (e.g., "CSE M.Tech" should match if "CSE" is allowed)
      if (validDepartments.some(valid => label.includes(valid) || valid.includes(label))) {
        return true;
      }
      return false;
    });

    // If filtering resulted in no departments, show all (fallback for data mismatches)
    if (filtered.length === 0 && departments.length > 0) {
      return departments;
    }

    return filtered;
  }, [formValues.programme, departments]);

  // Check if current department is invalid for selected programme
  const departmentMismatch = useMemo(() => {
    if (!formValues.programme || !formValues.department) return false;

    const validDepartments = PROGRAMME_DEPARTMENT_MAPPING[formValues.programme] || [];
    const currentDepartment = departments.find(d => String(d.value) === String(formValues.department));

    return currentDepartment && !validDepartments.includes(currentDepartment.label);
  }, [formValues.programme, formValues.department, departments]);

  const handleManualSubmit = (e) => {
    if (e) e.preventDefault();

    // Validate programme-department constraint
    if (formValues.programme && formValues.department) {
      const validDepartments = PROGRAMME_DEPARTMENT_MAPPING[formValues.programme] || [];
      const currentDepartment = departments.find(d => String(d.value) === String(formValues.department));

      if (currentDepartment && !validDepartments.includes(currentDepartment.label)) {
        alert(`Invalid combination! ${currentDepartment.label} department is not offered in ${formValues.programme} programme.`);
        return;
      }
    }

    // Manual form submission — no file
    onSubmit({ formValues, file: null });
  };

  const handleCSVSubmit = () => {
    // CSV submission — pass file, ignore form fields
    onSubmit({ formValues, file });
  };

  return (
    <>
      <Progress value={progress} color="blue" mb="md" />

      <Grid gutter="md">
        {/* Roll Number */}
        <Grid.Col span={6}>
          <TextInput
            label="Roll Number"
            placeholder="Leave blank to auto-generate"
            value={formValues.username}
            onChange={(e) => handleChange('username', e.target.value)}
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
            placeholder="Enter last name / NA"
            value={formValues.last_name}
            onChange={(e) => handleChange('last_name', e.target.value)}
            required
          />
        </Grid.Col>

        {/* Title */}
        <Grid.Col span={6}>
          <Select
            label="Title"
            placeholder="Select title"
            data={TITLE_OPTIONS}
            value={formValues.title}
            onChange={(value) => handleChange('title', value)}
          />
        </Grid.Col>

        {/* Programme — must come before Department so filtering works */}
        <Grid.Col span={6}>
          <Select
            label="Programme"
            placeholder="Select programme"
            data={PROGRAMMES}
            value={formValues.programme}
            onChange={(value) => {
              handleChange('programme', value);
              // Only clear department if it's not valid for the new programme
              if (formValues.department) {
                const validDepartments = PROGRAMME_DEPARTMENT_MAPPING[value] || [];
                const currentDepartment = departments.find(d => String(d.value) === String(formValues.department));
                if (currentDepartment && !validDepartments.includes(currentDepartment.label)) {
                  handleChange('department', '');
                }
              }
              if (onProgrammeChange) {
                onProgrammeChange(value);
              }
            }}
            required
          />
        </Grid.Col>

        {/* Batch */}
        <Grid.Col span={6}>
          <Select
            label="Batch"
            placeholder="Select batch"
            data={batches}
            value={formValues.batch ? `${formValues.batch}` : null}
            onChange={(value) => handleChange('batch', Number(value))}
            required
          />
        </Grid.Col>

        {/* Department */}
        <Grid.Col span={12}>
          <Select
            label="Department"
            placeholder="Select department"
            data={availableDepartments}
            value={formValues.department ? `${formValues.department}` : null}
            onChange={(value) => handleChange('department', Number(value))}
            searchable
            disabled={!formValues.programme}
            error={departmentMismatch}
            description={departmentMismatch ? "This department is not offered in the selected programme" : ""}
          />
          {departmentMismatch && (
            <Alert color="red" size="sm" mt="xs">
              <Text size="sm">
                ⚠️ <strong>{departments.find(d => String(d.value) === String(formValues.department))?.label}</strong> is not offered in <strong>{formValues.programme}</strong> programme.
                Please select a different department or programme.
              </Text>
            </Alert>
          )}
          {formValues.programme && availableDepartments.length === 0 && (
            <Alert color="yellow" size="sm" mt="xs">
              <Text size="sm">
                ℹ️ No departments available for <strong>{formValues.programme}</strong> programme.
              </Text>
            </Alert>
          )}
        </Grid.Col>

        {/* Gender */}
        <Grid.Col span={12}>
          <Text fw={500} size="sm" mb="xs">Gender *</Text>
          <Group spacing="sm">
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

        {/* Category */}
        <Grid.Col span={12}>
          <Select
            label="Category"
            placeholder="Select category"
            data={CATEGORIES}
            value={formValues.category}
            onChange={(value) => handleChange('category', value)}
            required
          />
        </Grid.Col>

        {/* Father's Name */}
        <Grid.Col span={6}>
          <TextInput
            label="Father's Name"
            placeholder="Enter father's name"
            value={formValues.father_name}
            onChange={(e) => handleChange('father_name', e.target.value)}
            required
          />
        </Grid.Col>

        {/* Mother's Name */}
        <Grid.Col span={6}>
          <TextInput
            label="Mother's Name"
            placeholder="Enter mother's name"
            value={formValues.mother_name}
            onChange={(e) => handleChange('mother_name', e.target.value)}
            required
          />
        </Grid.Col>

        {/* Date of Birth */}
        <Grid.Col span={6}>
          <DateInput
            label="Date of Birth"
            placeholder="Select date of birth"
            value={formValues.dob}
            onChange={(value) => handleChange('dob', value)}
          />
        </Grid.Col>

        {/* Phone */}
        <Grid.Col span={6}>
          <TextInput
            label="Phone"
            placeholder="Enter phone number"
            value={formValues.phone}
            onChange={(e) => handleChange('phone', e.target.value)}
          />
        </Grid.Col>

        {/* Address */}
        <Grid.Col span={12}>
          <TextInput
            label="Address"
            placeholder="Enter address"
            value={formValues.address}
            onChange={(e) => handleChange('address', e.target.value)}
          />
        </Grid.Col>

        {/* Personal / Alternate Email */}
        <Grid.Col span={12}>
          <TextInput
            label="Personal / Alternate Email"
            placeholder="Enter email for credential delivery"
            value={formValues.personal_email}
            onChange={(e) => handleChange('personal_email', e.target.value)}
            required
          />
        </Grid.Col>

        {/* Manual Submit Button */}
        <Grid.Col span={12}>
          <Button
            fullWidth
            size="md"
            mt="sm"
            loading={loading}
            onClick={handleManualSubmit}
          >
            Add Student
          </Button>
        </Grid.Col>
      </Grid>

      {/* CSV Upload Section */}
      <Divider mt="xl" labelPosition="center" label={<FaDiceD6 size={12} />} />

      <Stack justify="center" align="center" mt="lg">
        <Title order={3}>Through CSV</Title>
        <FileInput
          value={file}
          onChange={setFile}
          size="md"
          radius="xs"
          placeholder="Upload CSV"
          w="50%"
        />
        <Button onClick={handleCSVSubmit} w="50%" mt="sm" size="md" disabled={!file}>
          Create Students
        </Button>
        <Button
          variant="light"
          color="gray"
          onClick={onDownloadSampleCSV}
        >
          Download Sample CSV
        </Button>
      </Stack>
    </>
  );
};

export default StudentForm;

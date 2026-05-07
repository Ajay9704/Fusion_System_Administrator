import React, { useState, useEffect } from 'react';
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
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { FaDiceD6 } from 'react-icons/fa';
import { TITLE_OPTIONS, PROGRAMMES, CATEGORIES, GENDER_OPTIONS } from '../../utils/constants';
import { getDepartmentsByProgramme } from '../../services/roleService';

const StudentForm = ({ 
  initialValues, 
  onSubmit, 
  departments, 
  batches,
  onDownloadSampleCSV,
  loading = false 
}) => {
  const [formValues, setFormValues] = useState({
    ...initialValues,
    personal_email: initialValues.personal_email || ''
  });
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [predictedEmail, setPredictedEmail] = useState('');
  const [filteredDepartments, setFilteredDepartments] = useState([]);

  useEffect(() => {
    const totalFields = Object.keys(formValues).length;
    const filledFields = Object.values(formValues).filter((value) => value).length;
    setProgress((filledFields / totalFields) * 100);
  }, [formValues]);

  // Filter departments when programme changes
  useEffect(() => {
    const fetchFilteredDepartments = async () => {
      if (!formValues.programme) {
        setFilteredDepartments([]);
        setFormValues(prev => ({ ...prev, department: '' }));
        return;
      }

      try {
        console.log(`Fetching departments for programme: ${formValues.programme}`);
        const response = await getDepartmentsByProgramme(formValues.programme);
        
        console.log('Departments API response:', response);
        
        // Check if we got departments from the API
        if (response && response.length > 0) {
          const deptOptions = response.map(dept => ({
            value: `${dept.id}`,
            label: dept.name
          }));
          setFilteredDepartments(deptOptions);
          console.log(`Found ${deptOptions.length} departments for ${formValues.programme}`);
        } else {
          // Fallback: Use all departments if no filtered results
          console.warn(`No departments found for programme "${formValues.programme}", showing all academic departments`);
          const deptOptions = departments.map(dept => ({
            value: `${dept.value}`,
            label: dept.label
          }));
          setFilteredDepartments(deptOptions);
        }
        
        // Reset department selection when programme changes
        setFormValues(prev => ({ ...prev, department: '' }));
      } catch (error) {
        console.error('Error fetching departments:', error);
        // Fallback to all departments on error
        const deptOptions = departments.map(dept => ({
          value: `${dept.value}`,
          label: dept.label
        }));
        setFilteredDepartments(deptOptions);
      }
    };

    fetchFilteredDepartments();
  }, [formValues.programme, departments]);

  // Predict college email when batch, programme, and department are selected
  useEffect(() => {
    if (!formValues.username && formValues.batch && formValues.department && formValues.programme) {
      // Will be auto-generated, show preview
      setPredictedEmail('Auto-generated on submission');
    } else if (formValues.username) {
      setPredictedEmail(`${formValues.username.toLowerCase()}@iiitdmj.ac.in`);
    } else {
      setPredictedEmail('');
    }
  }, [formValues.username, formValues.batch, formValues.department, formValues.programme]);

  const handleChange = (field, value) => {
    setFormValues((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleFileChange = (file) => {
    setFile(file);
  };

  const handleSubmit = (e) => {
    if (e && e.preventDefault) e.preventDefault();
    onSubmit({ formValues, file });
  };

  return (
    <>
      <Progress value={progress} color="blue" mb="md" />

      <Grid gutter="md">
        {/* Personal Email - Required */}
        <Grid.Col span={12}>
          <TextInput
            label="Personal Email"
            placeholder="student.email@gmail.com"
            value={formValues.personal_email}
            onChange={(e) => handleChange('personal_email', e.target.value)}
            required
            description="Login credentials will be sent to this email"
          />
        </Grid.Col>

        {/* Roll Number - Optional (Auto-generated if blank) */}
        <Grid.Col span={6}>
          <TextInput
            label="Roll Number (Optional)"
            placeholder="Leave blank for auto-generation"
            value={formValues.username}
            onChange={(e) => handleChange('username', e.target.value)}
            description="Auto-generated from batch, programme & discipline"
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

        {/* Programme - MUST BE FIRST to filter departments */}
        <Grid.Col span={6}>
          <Select
            label="Programme"
            placeholder="Select programme"
            data={PROGRAMMES}
            value={formValues.programme}
            onChange={(value) => handleChange('programme', value)}
            required
            description="Select programme to filter available departments"
          />
        </Grid.Col>

        {/* Batch */}
        <Grid.Col span={6}>
          <Select
            label="Batch (Year)"
            placeholder="Select batch"
            data={batches}
            value={`${formValues.batch}`}
            onChange={(value) => handleChange('batch', Number(value))}
            required
          />
        </Grid.Col>

        {/* Department - Filtered based on Programme */}
        <Grid.Col span={12}>
          <Select
            label="Department / Discipline *"
            placeholder={formValues.programme ? "Select department" : "Select programme first"}
            data={filteredDepartments}
            value={`${formValues.department}`}
            onChange={(value) => handleChange('department', Number(value))}
            required
            disabled={!formValues.programme || filteredDepartments.length === 0}
            searchable
            clearable
            description={filteredDepartments.length > 0 
              ? `${filteredDepartments.length} department(s) available for ${formValues.programme}`
              : formValues.programme 
                ? "Loading departments..."
                : "Select a programme to see available departments"
            }
            error={!formValues.programme ? "Please select a programme first" : 
                   filteredDepartments.length === 0 && formValues.programme ? "No departments available" : null}
          />
        </Grid.Col>

        {/* Gender */}
        <Grid.Col span={12}>
          <Radio.Group
            label="Gender"
            value={formValues.sex}
            onChange={(value) => handleChange('sex', value)}
            required
          >
            <Group spacing="sm" position="apart" mt="xs">
              {GENDER_OPTIONS.map((option) => (
                <Radio key={option.value} value={option.value} label={option.label} />
              ))}
            </Group>
          </Radio.Group>
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

        {/* College Email Preview */}
        {predictedEmail && (
          <Grid.Col span={12}>
            <TextInput
              label="College Email (Preview)"
              value={predictedEmail}
              disabled
              description="Student's official institute email address"
            />
          </Grid.Col>
        )}
      </Grid>

      {/* Individual Submit Button */}
      <Button
        onClick={() => handleSubmit({ formValues, file: null })}
        mt="xl"
        size="lg"
        fullWidth
        variant="gradient"
        gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
        disabled={loading || !formValues.personal_email || !formValues.first_name || !formValues.last_name}
      >
        {loading ? 'Creating Student...' : 'Create Student'}
      </Button>

      {/* CSV Upload Section */}
      <Divider mt="xl" labelPosition="center" label={<FaDiceD6 size={12} />} />

      <Stack justify="center" align="center" mt="lg" spacing="md">
        <Title order={3}>Bulk Upload Students</Title>
        <Text size="sm" c="dimmed" align="center">
          Upload a CSV file to create multiple students at once
        </Text>
        <FileInput
          value={file}
          onChange={handleFileChange}
          size="md"
          radius="xs"
          placeholder="Upload CSV file"
          w="50%"
        />
        <Button 
          onClick={() => handleSubmit()} 
          w="50%" 
          mt="sm" 
          size="md"
          disabled={!file}
          variant="gradient"
          gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
        >
          Bulk Upload Students
        </Button>
        <Button
          variant="light"
          color="gray"
          onClick={onDownloadSampleCSV}
          size="sm"
        >
          Download Sample CSV
        </Button>
      </Stack>
    </>
  );
};

export default StudentForm;

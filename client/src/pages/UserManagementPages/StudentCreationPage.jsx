import React, { useState, useEffect } from "react";
import {
  Button,
  Box,
  Title,
  Flex,
  Divider,
  Paper,
  Group,
} from "@mantine/core";
import { FaCheck, FaDiceD6, FaTimes, FaUpload } from "react-icons/fa";
import { rem } from "@mantine/core";
import { showNotification } from "@mantine/notifications";
import { useMediaQuery } from "@mantine/hooks";
import { getAllDepartments, getDepartmentsByProgramme, getAllBatches } from '../../services/roleService';
import { createStudent, bulkUploadUsers, downloadSampleCSV } from "../../services/userService";
import StudentForm from '../../components/forms/StudentForm';
import BulkUploadModal from '../../components/BulkUploadModal/BulkUploadModal';
import { formatDateForAPI } from '../../utils/dateUtils';
import { getErrorMessage, showErrorNotification, showSuccessNotification } from '../../utils/errorHandler';

const StudentCreationPage = () => {
  const xIcon = <FaTimes style={{ width: rem(20), height: rem(20) }} />;
  const checkIcon = <FaCheck style={{ width: rem(20), height: rem(20) }} />;

  const [formValues, setFormValues] = useState({
    username: "",
    first_name: "",
    last_name: "",
    sex: "",
    category: "",
    father_name: "",
    mother_name: "",
    programme: "",
    batch: "",
    department: '',
    title: '',
    designation: '',
    dob: null,
    phone: '',
    address: '',
    personal_email: '',
  });

  const [departments, setDepartments] = useState([]);
  const [batches, setBatches] = useState([]);
  const [bulkUploadModalOpen, setBulkUploadModalOpen] = useState(false);

  const matches = useMediaQuery("(min-width: 768px)");

  useEffect(() => {
    fetchDepartments();
    fetchBatches();
  }, []);

  const fetchDepartments = async (programme = null) => {
    try {
      let response;
      if (programme) {
        response = await getDepartmentsByProgramme(programme);
      } else {
        response = await getAllDepartments();
      }
      const all_departments = response.map(d => ({ value: `${d.id}`, label: d.name }));
      setDepartments(all_departments);
    } catch (error) {
      // If filtered fetch fails, fall back to all departments
      if (programme) {
        try {
          const fallback = await getAllDepartments();
          setDepartments(fallback.map(d => ({ value: `${d.id}`, label: d.name })));
        } catch (e) {
          showErrorNotification(e, 'Department Error');
        }
      } else {
        showErrorNotification(error, 'Department Error');
      }
    }
  }

  const fetchBatches = async () => {
    try {
      let all_batches = [];
      const response = await getAllBatches();
      // Create unique options based on year to avoid duplicates
      const uniqueYears = [...new Set(response.map(batch => batch.year))];
      for(let i=0; i<uniqueYears.length; i++){
        all_batches[i] = {value: `${uniqueYears[i]}`, label: `${uniqueYears[i]}`}
      }
      setBatches(all_batches);
    } catch (error) {
      showErrorNotification(error, 'Batch Error');
    }
  }

  const handleProgrammeChange = async (value) => {
    setFormValues((prev) => ({
      ...prev,
      programme: value,
      // Don't clear department - let the form handle constraint validation
    }));

    await fetchDepartments(value);
  };

  const handleDownloadSampleCSV = async () => {
    try {
      await downloadSampleCSV();
    } catch (error) {
      showErrorNotification(error, 'Download Error');
    }
  };

  const handleSubmit = async ({ formValues, file }) => {
    try {
      let response;
      if(file){
        const formData = new FormData();
        formData.append('file', file);
        response = await bulkUploadUsers(formData);
      }
      else {
        if (!formValues.personal_email || !formValues.personal_email.trim()) {
          showErrorNotification({ message: 'Personal email is required for credential delivery.' }, 'Validation Error');
          return;
        }

        // Prepare form values for API
        const formattedValues = {
          ...formValues,
          dob: formatDateForAPI(formValues.dob),
        };

        // Handle username generation - if empty or whitespace, remove it so backend can auto-generate
        if (!formattedValues.username || !formattedValues.username.trim()) {
          delete formattedValues.username;
        } else {
          // Clean up username if provided
          formattedValues.username = formattedValues.username.trim();
        }

        // Remove empty values to avoid validation issues
        Object.keys(formattedValues).forEach(key => {
          if (formattedValues[key] === '' || formattedValues[key] === null) {
            delete formattedValues[key];
          }
        });

        response = await createStudent(formattedValues);
      }

      if(response.skipped_users_count > 0){
        const csvUrl = URL.createObjectURL(new Blob([response.skipped_users_csv], {type: 'text/csv'}));
        downloadCSV(csvUrl, 'skipped_users.csv');
      }
      
      showSuccessNotification(`${response.created_users.length} Student(s) created successfully.${response.skipped_users_count ? ` ${response.skipped_users_count} user(s) skipped.` : ''}`);

      // Reset form only if single student creation
      if (!file) {
        setFormValues({
          username: "",
          first_name: "",
          last_name: "",
          sex: "",
          category: "",
          father_name: "",
          mother_name: "",
          programme: "",
          batch: "",
          department: '',
          title: '',
          designation: '',
          dob: null,
          phone: '',
          address: '',
          personal_email: '',
        });
      }
    } catch (err) {
      showErrorNotification(err, 'Creation Error');
    }
  };

  const downloadCSV = (url, filename) => {
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <Box maw={700} mx="auto" p="lg" shadow="sm">
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
              Add Student
            </Title>
          </Button>
        </Flex>

        <Divider my="sm" />

        <StudentForm
          initialValues={formValues}
          onSubmit={handleSubmit}
          departments={departments}
          batches={batches}
          onProgrammeChange={handleProgrammeChange}
          onDownloadSampleCSV={handleDownloadSampleCSV}
          onOpenBulkUpload={() => setBulkUploadModalOpen(true)}
        />
      </Paper>

      <BulkUploadModal
        opened={bulkUploadModalOpen}
        onClose={() => setBulkUploadModalOpen(false)}
        onUpload={bulkUploadUsers}
        onDownloadSample={handleDownloadSampleCSV}
      />
    </Box>
  );
};

export default StudentCreationPage;

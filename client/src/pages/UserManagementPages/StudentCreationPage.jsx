import React, { useState, useEffect } from "react";
import {
  Button,
  Box,
  Title,
  Flex,
  Divider,
  Paper,
} from "@mantine/core";
import { FaCheck, FaDiceD6, FaTimes } from "react-icons/fa";
import { rem } from "@mantine/core";
import { showNotification } from "@mantine/notifications";
import { useMediaQuery } from "@mantine/hooks";
import { getAllDepartments, getAllBatches } from '../../services/roleService';
import { createStudent, bulkUploadUsers, downloadSampleCSV } from "../../services/userService";
import StudentForm from '../../components/forms/StudentForm';

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

  const matches = useMediaQuery("(min-width: 768px)");

  useEffect(() => {
    fetchDepartments();
    fetchBatches();
  }, []);

  const fetchDepartments = async () => {
    try {
      let all_departments = [];
      const response = await getAllDepartments('student');
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

  const fetchBatches = async () => {
    try {
      let all_batches = [];
      const response = await getAllBatches();
      for(let i=0; i<response.length; i++){
        all_batches[i] = `${response[i].year}`
      }
      setBatches(all_batches);
    } catch (error) {
      showNotification({
        title: 'Error',
        icon: xIcon,
        position: "top-center",
        withCloseButton: true,
        message: 'An error occurred while fetching batches.',
        color: 'red',
      });
    }
  }

  const handleDownloadSampleCSV = async () => {
    try {
      await downloadSampleCSV();
    } catch (error) {
      showNotification({
        title: 'Error',
        icon: xIcon,
        position: "top-center",
        withCloseButton: true,
        message: 'Failed to download sample CSV',
        color: 'red',
      });
    }
  };

  const handleSubmit = async ({ formValues, file }) => {
    try {
      let response;
      if(file){
        // Bulk upload
        const formData = new FormData();
        formData.append('file', file);
        response = await bulkUploadUsers(formData);
        
        // Handle bulk upload response
        if(response.created_count > 0 || response.failed_count > 0) {
          const message = `${response.created_count} student(s) created successfully. ${response.failed_count > 0 ? `${response.failed_count} failed.` : ''}`;
          
          showNotification({
            icon: checkIcon,
            title: "Bulk Upload Complete",
            position: "top-center",
            withCloseButton: true,
            autoClose: 8000,
            message: message,
            color: response.failed_count > 0 ? "yellow" : "green",
          });
          
          // Download failed entries CSV if exists
          if (response.failed_csv && response.failed_count > 0) {
            const csvUrl = URL.createObjectURL(new Blob([response.failed_csv], {type: 'text/csv'}));
            downloadCSV(csvUrl, `failed_entries_${Date.now()}.csv`);
            
            setTimeout(() => {
              showNotification({
                icon: xIcon,
                title: "Failed Entries Report Downloaded",
                message: "Check the downloaded CSV for details. Fix errors and re-upload.",
                position: "top-center",
                withCloseButton: true,
                autoClose: 6000,
                color: "red",
              });
            }, 1000);
          }
        }
      }
      else {
        // Individual student creation
        response = await createStudent(formValues);
        
        showNotification({
          icon: checkIcon,
          title: "Student Created",
          position: "top-center",
          withCloseButton: true,
          autoClose: 5000,
          message: `Student ${response.username || 'created'} successfully. Credentials sent to ${formValues.personal_email}`,
          color: "green",
        });
        
        // Reset form
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
      const errorMessage = err.response
        ? `${JSON.stringify(err.response.data.error) || JSON.stringify(err.response.data.data) || JSON.stringify(err.response.data.message)}`
        : err.request
        ? "No response received from the server"
        : `${err.message}`;

      showNotification({
        title: "Error",
        icon: xIcon,
        position: "top-center",
        withCloseButton: true,
        message: errorMessage,
        color: "red",
      });
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
          onDownloadSampleCSV={handleDownloadSampleCSV}
        />
      </Paper>
    </Box>
  );
};

export default StudentCreationPage;

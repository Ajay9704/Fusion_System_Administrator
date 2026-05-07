import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMediaQuery } from "@mantine/hooks";
import { FaUserAlt, FaClone, FaBook, FaUserGraduate, FaChalkboardTeacher, FaUsersCog, FaKey, FaUserShield, FaTasks, FaEdit, FaArchive as FaArchiveIcon, FaClipboardList, FaShieldAlt, FaHourglassHalf } from "react-icons/fa";
import { Tooltip, Flex } from "@mantine/core";
import ProfileHeader from '../ProfileHeader/ProfileHeader';

const MANTINE_BLUE = "#228be6";
const MANTINE_DARK_BLUE = "#1c7ed6";

const Sidebar = () => {
  const navigate = useNavigate();
  const isSmallScreen = useMediaQuery("(max-width: 768px)");
  const [hovered, setHovered] = useState(null);

  const menuItems = [
    {
      label: "User Directory",
      icon: <FaBook size={24} />,
      height: "10%",
      isPrimary: true,
      action: () => navigate("/UserDirectory"),
    },
    {
      label: "User Management",
      icon: <FaUserAlt size={24} />,
      menuKey: "user",
      subItems: [
        { label: "Add Student", path: "/UserManagement/CreateStudent", icon: <FaUserGraduate size={18} /> },
        { label: "Add Faculty", path: "/UserManagement/CreateFaculty", icon: <FaChalkboardTeacher size={18} /> },
        { label: "Add Staff", path: "/UserManagement/CreateStaff", icon: <FaUsersCog size={18} /> },
        { label: "Reset Password", path: "/UserManagement/ResetUserPassword", icon: <FaKey size={18} /> },
      ],
    },
    {
      label: "Role Management",
      icon: <FaClone size={24} />,
      menuKey: "role",
      subItems: [
        { label: "Create Role", path: "/RoleManagement/CreateCustomRole", icon: <FaUserShield size={18} /> },
        { label: "Manage Role Access", path: "/RoleManagement/ManageRoleAccess", icon: <FaTasks size={18} /> },
        { label: "Edit Role", path: "/RoleManagement/EditUserRole", icon: <FaEdit size={18} /> },
      ],
    },
    {
      label: "Archive Management",
      icon: <FaArchiveIcon size={24} />,
      menuKey: "archive",
      subItems: [
        { label: "Archive Students", path: "/archive/students", icon: <FaArchiveIcon size={18} /> },
        { label: "Archive Faculty", path: "/archive/faculty", icon: <FaArchiveIcon size={18} /> },
      ],
    },
    {
      label: "Audit Logs",
      icon: <FaClipboardList size={24} />,
      menuKey: "audit",
      height: "10%",
      isPrimary: true,
      action: () => navigate("/AuditLogs"),
    },
    {
      label: "RBAC Dashboard",
      icon: <FaShieldAlt size={24} />,
      menuKey: "rbac",
      height: "10%",
      isPrimary: true,
      action: () => navigate("/RBAC"),
    },
    {
      label: "Emergency Access",
      icon: <FaHourglassHalf size={24} />,
      menuKey: "emergency",
      height: "10%",
      isPrimary: true,
      action: () => navigate("/emergency-access"),
    },
  ];

  return (
    <Flex
      direction="column"
      align="center"
      style={{
        position: "fixed",
        right: 0,
        top: 0,
        height: "100vh",
        width: isSmallScreen ? "60px" : "80px",
        backgroundColor: "#ffffff",
        boxShadow: "-3px 0 10px rgba(0, 0, 0, 0.1)",
      }}
    >
      {/* Profile Header at Top of Sidebar */}
      <div style={{ 
        width: '100%', 
        padding: '8px',
      }}>
        <ProfileHeader />
      </div>

      {menuItems.map(({ label, icon, path, menuKey, subItems, isPrimary, height, isDashboard, action }) => (
        <Tooltip key={label} label={label} position="left" withArrow disabled={hovered === menuKey && subItems}>
          <div
            style={{
              width: "100%",
              height: height || "30%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              position: "relative",
              backgroundColor:
                isDashboard || isPrimary
                  ? hovered === label
                    ? MANTINE_DARK_BLUE
                    : MANTINE_BLUE
                  : hovered === menuKey || hovered === label
                    ? MANTINE_BLUE
                    : "transparent",
              transition: "background 0.3s ease-in-out",
              cursor: "pointer",
              color:
                isDashboard || hovered === menuKey || hovered === label || isPrimary
                  ? "white"
                  : MANTINE_BLUE,
            }}
            onMouseEnter={() => setHovered(menuKey || label)}
            onMouseLeave={() => setHovered(null)}
            onClick={() => (action ? action() : path && navigate(path))}
          >
            {hovered === menuKey && subItems ? (
              <Flex direction="column" align="center" style={{ width: "100%", height: "100%" }}>
                {subItems.map(({ label, path, icon }) => (
                  <Tooltip key={label} label={label} position="left" withArrow>
                    <div
                      style={{
                        flex: 1,
                        width: "100%",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        backgroundColor: MANTINE_DARK_BLUE,
                        transition: "background 0.3s ease-in-out",
                        color: "white",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = MANTINE_BLUE)}
                      onMouseLeave={(e) => (e.currentTarget.style.background = MANTINE_DARK_BLUE)}
                      onClick={() => navigate(path)}
                    >
                      {icon}
                    </div>
                  </Tooltip>
                ))}
              </Flex>
            ) : (
              <div style={{ color: "inherit" }}>{icon}</div>
            )}
          </div>
        </Tooltip>
      ))}
    </Flex>
  );
};

export default Sidebar;

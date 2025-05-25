import streamlit as st
import pandas as pd
import copy 
from datetime import datetime
import io
import base64

# --- Page Config ---
st.set_page_config(
    page_title="Honorians InSync - ASRMS",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Modern Design ---
st.markdown("""
<style>
    /* Modern Color Scheme */
    :root {
        --primary-color: #2E86AB;
        --secondary-color: #A23B72;
        --success-color: #27AE60;
        --warning-color: #F39C12;
        --danger-color: #E74C3C;
        --dark-bg: #1a1a1a;
        --light-bg: #f8f9fa;
    }
    
    /* Main Container Styling */
    .main {
        padding: 1rem;
        background-color: var(--light-bg);
    }
    
    /* Card-like containers */
    .stExpander {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border: none !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #236b8e;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #f0f2f6;
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 20px;
        background-color: white;
        border-radius: 5px;
        color: #333;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Schedule Table */
    table.schedule_table {
        border-collapse: collapse;
        width: 100%;
        background-color: white;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    table.schedule_table th, table.schedule_table td {
        border: 1px solid #e0e0e0;
        padding: 12px;
        text-align: center;
        vertical-align: middle;
        font-size: 0.85em;
    }
    
    table.schedule_table th {
        background-color: var(--primary-color);
        color: white;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    table.schedule_table td:first-child {
        background-color: #f8f9fa;
        font-weight: 600;
        color: var(--primary-color);
    }
    
    table.schedule_table td {
        transition: background-color 0.3s ease;
    }
    
    table.schedule_table td:hover {
        background-color: #f0f8ff;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
        border-radius: 5px;
        padding: 0.75rem 1.25rem;
    }
    
    .stError {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
        border-radius: 5px;
        padding: 0.75rem 1.25rem;
    }
    
    .stWarning {
        background-color: #fff3cd;
        border-color: #ffeaa7;
        color: #856404;
        border-radius: 5px;
        padding: 0.75rem 1.25rem;
    }
    
    /* File Uploader */
    .uploadedFile {
        background-color: white;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    /* Workflow Cards */
    .workflow-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        height: 100%;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .workflow-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    .workflow-card h4 {
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }
    
    /* Data Blueprint Cards */
    .data-blueprint-item {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
        border-left: 4px solid var(--primary-color);
    }
    
    .item-label {
        font-weight: 600;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }
    
    .item-headers {
        font-size: 0.9em;
        color: #666;
    }
    
    /* Conflict Resolution Cards */
    .conflict-card {
        background-color: #fff5f5;
        border-left: 4px solid var(--danger-color);
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    
    /* Print Styles */
    @media print {
        .stButton, .stSelectbox, .stFileUploader, .stSidebar {
            display: none !important;
        }
        
        table.schedule_table {
            box-shadow: none;
            page-break-inside: avoid;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Function Definitions ---
DAYS_ORDER = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

TIME_SLOTS_ORDER_24HR = [
    "7:00-8:00", "8:00-9:00", "9:00-10:00", "10:00-11:00", 
    "11:00-12:00", "12:00-13:00", "13:00-14:00", "14:00-15:00", 
    "15:00-16:00", "16:00-17:00", "17:00-18:00"
]

def clean_html_for_export(html_string):
    """Remove HTML tags from string for clean CSV export."""
    if not html_string:
        return ''
    
    # Remove HTML tags
    import re
    
    # First, replace <br> and </div> with newlines
    cleaned = html_string.replace('<br>', '\n').replace('</div>', '\n')
    
    # Remove all HTML tags
    cleaned = re.sub('<[^<]+?>', '', cleaned)
    
    # Clean up multiple newlines
    cleaned = re.sub('\n+', '\n', cleaned).strip()
    
    return cleaned

def export_timetable_as_csv(schedule_df, entity_type=None, selected_entity=None):
    """Create a CSV-friendly version of the timetable."""
    if schedule_df is None or schedule_df.empty:
        return "No data to export"
    
    # Filter the schedule based on selection
    filtered_schedule = schedule_df.copy()
    filtered_schedule['Day'] = filtered_schedule['Day'].str.upper()
    
    if entity_type and selected_entity and selected_entity != "All":
        if entity_type == "Room":
            filtered_schedule = filtered_schedule[filtered_schedule['Room'] == selected_entity]
        elif entity_type == "Section":
            filtered_schedule = filtered_schedule[filtered_schedule['Section'] == selected_entity]
        elif entity_type == "Instructor":
            filtered_schedule = filtered_schedule[filtered_schedule['Instructor'] == selected_entity]
    
    if filtered_schedule.empty:
        return "No data matches the current filter"
    
    # Create timetable structure
    timetable_data = {}
    
    for _, row in filtered_schedule.iterrows():
        time_slot = row['Time Slot']
        day = row['Day']
        
        if time_slot not in timetable_data:
            timetable_data[time_slot] = {d: [] for d in DAYS_ORDER}
        
        # Create cell content
        cell_info = f"{row['Subject Code']}"
        if entity_type == "Section":
            cell_info += f" | Room: {row['Room']} | Prof: {row['Instructor']}"
        elif entity_type == "Instructor":
            cell_info += f" | Room: {row['Room']} | Sec: {row['Section']}"
        elif entity_type == "Room":
            cell_info += f" | Sec: {row['Section']} | Prof: {row['Instructor']}"
        else:
            cell_info += f" | {row['Section']} | {row['Instructor']} | {row['Room']}"
        
        timetable_data[time_slot][day].append(cell_info)
    
    # Convert to DataFrame
    rows = []
    for time_slot in TIME_SLOTS_ORDER_24HR:
        if time_slot in timetable_data:
            row_data = {'Time': format_time_slot_for_display(time_slot)}
            for day in DAYS_ORDER:
                entries = timetable_data[time_slot].get(day, [])
                row_data[day] = ' || '.join(entries) if entries else ''
            rows.append(row_data)
    
    timetable_df = pd.DataFrame(rows)
    
    # Add header information
    header_info = f"DHVSU Class Schedule - Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n"
    if entity_type and selected_entity and selected_entity != "All":
        header_info += f"{entity_type}: {selected_entity}\n"
    header_info += "\n"
    
    # Convert to CSV
    csv_content = header_info + timetable_df.to_csv(index=False)
    
    return csv_content

def get_color_for_subject(subject_code, subject_codes_list=None):
    """Generate a consistent color for each subject code."""
    # Define a palette of distinct colors
    color_palette = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57',
        '#FF9FF3', '#54A0FF', '#48DBFB', '#1DD1A1', '#FFA502',
        '#5F27CD', '#00D2D3', '#A29BFE', '#FD79A8', '#FDCB6E',
        '#6C5CE7', '#A8E6CF', '#FFD3B6', '#FF8B94', '#C7CEEA',
        '#B2EBF2', '#DCEDC8', '#FFE0B2', '#F8BBD0', '#E1BEE7',
        '#C5E1A5', '#FFCCBC', '#D7CCC8', '#CFD8DC', '#B39DDB'
    ]
    
    if subject_codes_list is None:
        # If no list provided, use hash to get consistent color
        hash_value = sum(ord(c) for c in subject_code)
        return color_palette[hash_value % len(color_palette)]
    else:
        # If list provided, assign colors in order
        if subject_code not in subject_codes_list:
            subject_codes_list.append(subject_code)
        index = subject_codes_list.index(subject_code)
        return color_palette[index % len(color_palette)]

def format_time_slot_for_display(time_slot_24hr):
    """Converts a 'HH:MM-HH:MM' 24-hour string to 'H:MM AM/PM - H:MM AM/PM'."""
    try:
        start_str, end_str = time_slot_24hr.split('-')
        start_dt = datetime.strptime(start_str, "%H:%M")
        end_dt = datetime.strptime(end_str, "%H:%M")
        
        start_display = start_dt.strftime("%I:%M %p").lstrip('0').replace(" 00", " 12")
        if start_display.startswith(":"): start_display = "12" + start_display

        end_display = end_dt.strftime("%I:%M %p").lstrip('0').replace(" 00", " 12")
        if end_display.startswith(":"): end_display = "12" + end_display

        return f"{start_display} - {end_display}"
    except ValueError:
        return time_slot_24hr

TIME_SLOTS_DISPLAY = [format_time_slot_for_display(ts) for ts in TIME_SLOTS_ORDER_24HR]

def check_manual_assignment_conflicts(schedule_df, new_class_details):
    """Enhanced conflict checking with section conflicts."""
    found_conflicts = []
    
    if schedule_df is None or schedule_df.empty:
        return []

    teacher = new_class_details['Instructor']
    room = new_class_details['Room']
    day = new_class_details['Day']
    time_slot = new_class_details['Time Slot']
    section = new_class_details.get('Section')

    # Check Teacher Conflict
    teacher_conflict = schedule_df[
        (schedule_df['Instructor'] == teacher) &
        (schedule_df['Day'] == day) &
        (schedule_df['Time Slot'] == time_slot)
    ]
    if not teacher_conflict.empty:
        conflicting_class = teacher_conflict.iloc[0]
        found_conflicts.append(
            f"Teacher Conflict: {teacher} is already scheduled for "
            f"{conflicting_class['Subject Code']} in section {conflicting_class['Section']} "
            f"at {day} {time_slot}."
        )

    # Check Room Conflict
    room_conflict = schedule_df[
        (schedule_df['Room'] == room) &
        (schedule_df['Day'] == day) &
        (schedule_df['Time Slot'] == time_slot)
    ]
    if not room_conflict.empty:
        conflicting_class = room_conflict.iloc[0]
        found_conflicts.append(
            f"Room Conflict: {room} is already scheduled for "
            f"{conflicting_class['Subject Code']} in section {conflicting_class['Section']} "
            f"at {day} {time_slot}."
        )
    
    # Check Section Conflict
    if section:
        section_conflict = schedule_df[
            (schedule_df['Section'] == section) &
            (schedule_df['Day'] == day) &
            (schedule_df['Time Slot'] == time_slot)
        ]
        if not section_conflict.empty:
            conflicting_class = section_conflict.iloc[0]
            found_conflicts.append(
                f"Section Conflict: {section} already has "
                f"{conflicting_class['Subject Code']} scheduled "
                f"at {day} {time_slot}."
            )
        
    return found_conflicts

def process_instructor_data(raw_df):
    if raw_df is None: return None
    parsed_instructors = {}
    for _, row in raw_df.iterrows():
        instructor_name = row['Instructor']
        day = row['Day']; time_slot = row['Time Slot']; specialization = row['Specialization']
        if instructor_name not in parsed_instructors:
            parsed_instructors[instructor_name] = {'availability': [], 'specializations': set()}
        parsed_instructors[instructor_name]['availability'].append((day, time_slot))
        parsed_instructors[instructor_name]['specializations'].add(specialization)
    return parsed_instructors

def process_room_data(raw_df):
    if raw_df is None: return None
    parsed_rooms = {}
    for _, row in raw_df.iterrows():
        room_name = row['Room']; day = row['Day']; time_slot = row['Time Slot']; capacity = row['Max Capacity']
        if room_name not in parsed_rooms: parsed_rooms[room_name] = {}
        parsed_rooms[room_name][(day, time_slot)] = {'capacity': int(capacity), 'is_available': True}
    return parsed_rooms

def get_classes_to_schedule(sections_df, subjects_df, curriculum_df):
    if sections_df is None or subjects_df is None or curriculum_df is None:
        st.warning("One or more required dataframes for generating class list not loaded.")
        return []
    classes_list = []
    subjects_lookup = subjects_df.set_index('Subject Code').to_dict('index')
    for _, section_row in sections_df.iterrows():
        section_course = section_row['Course']; section_year_level = section_row['Year Level']
        section_name = section_row['Section']; section_students = section_row['Students']
        relevant_curriculum = curriculum_df[
            (curriculum_df['Course'] == section_course) & (curriculum_df['Year Level'] == section_year_level)]
        for _, curriculum_row in relevant_curriculum.iterrows():
            subject_code = curriculum_row['Subject Code']
            if subject_code in subjects_lookup:
                subject_details = subjects_lookup[subject_code]
                classes_list.append({
                    'section_course': section_course, 'section_year_level': section_year_level,
                    'section_name': section_name, 'section_students': section_students,
                    'subject_code': subject_code, 'subject_name': subject_details['Subject Name'],
                    'required_specialization': subject_details['Required Specialization']})
            else:
                st.warning(f"Subject Code '{subject_code}' not found in subjects list for section {section_name}.")
    return classes_list

def generate_schedule_attempt(classes_to_schedule, parsed_instructors_orig, parsed_rooms_orig):
    """Enhanced scheduling with better conflict prevention."""
    if not classes_to_schedule or not parsed_instructors_orig or not parsed_rooms_orig:
        st.warning("Missing necessary data for scheduling.")
        return [], []

    current_instructors_data = copy.deepcopy(parsed_instructors_orig)
    current_rooms_availability = copy.deepcopy(parsed_rooms_orig)
    
    generated_schedule = []
    conflicts = []
    instructor_busy_slots = set()
    section_busy_slots = set()
    room_busy_slots = set()  # Enhanced: Track room busy slots
    
    # Sort by number of students (largest first)
    try:
        sorted_classes_to_schedule = sorted(
            classes_to_schedule,
            key=lambda x: x.get('section_students', 0), 
            reverse=True
        )
    except Exception as e:
        print(f"Error sorting classes: {e}. Using original order.")
        sorted_classes_to_schedule = classes_to_schedule

    for class_info in sorted_classes_to_schedule:
        section_name = class_info['section_name']
        subject_code = class_info['subject_code']
        subject_name = class_info['subject_name']
        required_spec = class_info['required_specialization']
        num_students = class_info['section_students']

        slot_assigned_for_this_class = False
        
        # Find specialized teachers
        specialized_teachers = [
            instr_name for instr_name, details in parsed_instructors_orig.items()
            if required_spec in details['specializations']
        ]
        
        if not specialized_teachers:
            conflicts.append({
                'type': 'Unscheduled Class', 
                'section': section_name, 
                'subject': subject_code,
                'students': num_students, 
                'required_specialization': required_spec,
                'reason': f"No teachers found with specialization: {required_spec}."
            })
            continue

        # Find suitable rooms
        suitable_rooms_by_capacity = []
        for room_name, room_slots in parsed_rooms_orig.items(): 
            if any(details['capacity'] >= num_students for details in room_slots.values()):
                suitable_rooms_by_capacity.append(room_name)
        
        if not suitable_rooms_by_capacity:
            conflicts.append({
                'type': 'Unscheduled Class', 
                'section': section_name, 
                'subject': subject_code,
                'students': num_students, 
                'required_specialization': required_spec,
                'reason': f"No rooms found with capacity >= {num_students} students."
            })
            continue

        # Try to assign the class
        for instructor_name in specialized_teachers:
            if slot_assigned_for_this_class: 
                break
            
            instr_details = current_instructors_data[instructor_name]
            
            for day, time_slot in list(instr_details['availability']):
                if slot_assigned_for_this_class: 
                    break
                
                # Enhanced checks
                if (instructor_name, day, time_slot) in instructor_busy_slots:
                    continue
                if (section_name, day, time_slot) in section_busy_slots:
                    continue
                
                for room_name in suitable_rooms_by_capacity:
                    if slot_assigned_for_this_class: 
                        break
                    
                    # Check if room is busy at this time
                    if (room_name, day, time_slot) in room_busy_slots:
                        continue
                    
                    if (day, time_slot) in current_rooms_availability.get(room_name, {}):
                        room_slot_details = current_rooms_availability[room_name][(day, time_slot)]
                        
                        if room_slot_details['is_available'] and room_slot_details['capacity'] >= num_students:
                            # Assign the class
                            generated_schedule.append({
                                'Section': section_name, 
                                'Subject Code': subject_code, 
                                'Subject Name': subject_name,
                                'Instructor': instructor_name, 
                                'Room': room_name, 
                                'Day': day, 
                                'Time Slot': time_slot,
                                'Students': num_students, 
                                'Room Capacity': room_slot_details['capacity']
                            })
                            
                            # Mark slots as busy
                            instructor_busy_slots.add((instructor_name, day, time_slot))
                            section_busy_slots.add((section_name, day, time_slot))
                            room_busy_slots.add((room_name, day, time_slot))
                            current_rooms_availability[room_name][(day, time_slot)]['is_available'] = False
                            
                            slot_assigned_for_this_class = True
                            break

        if not slot_assigned_for_this_class:
            conflicts.append({
                'type': 'Unscheduled Class', 
                'section': section_name, 
                'subject': subject_code,
                'students': num_students, 
                'required_specialization': required_spec,
                'reason': 'No common available time slot found for teacher, room, and section.'
            })
    
    # Verify no double bookings in final schedule
    schedule_df = pd.DataFrame(generated_schedule)
    if not schedule_df.empty:
        # Check for any remaining double bookings
        for idx, row in schedule_df.iterrows():
            same_teacher = schedule_df[
                (schedule_df.index != idx) &
                (schedule_df['Instructor'] == row['Instructor']) &
                (schedule_df['Day'] == row['Day']) &
                (schedule_df['Time Slot'] == row['Time Slot'])
            ]
            if not same_teacher.empty:
                conflicts.append({
                    'type': 'Teacher Double Booking',
                    'instructor': row['Instructor'],
                    'day': row['Day'],
                    'time_slot': row['Time Slot'],
                    'classes_involved': f"{row['Subject Code']} and {same_teacher.iloc[0]['Subject Code']}"
                })
            
    return generated_schedule, conflicts

def export_schedule_to_csv(schedule_df):
    """Export schedule to CSV format with enhanced formatting."""
    if schedule_df is None or schedule_df.empty:
        return None
    
    # Create a copy for export
    export_df = schedule_df.copy()
    
    # Add day ordering for proper sorting
    day_order = {day: i for i, day in enumerate(DAYS_ORDER)}
    export_df['day_order'] = export_df['Day'].map(day_order)
    
    # Sort by multiple criteria for better organization
    export_df = export_df.sort_values(['day_order', 'Time Slot', 'Room', 'Section'])
    
    # Remove the temporary sorting column
    export_df = export_df.drop('day_order', axis=1)
    
    # Reorder columns for better readability
    column_order = ['Day', 'Time Slot', 'Subject Code', 'Subject Name', 
                    'Section', 'Instructor', 'Room', 'Students', 'Room Capacity']
    
    # Only include columns that exist
    export_columns = [col for col in column_order if col in export_df.columns]
    export_df = export_df[export_columns]
    
    # Convert to CSV with proper formatting
    csv = export_df.to_csv(index=False, encoding='utf-8-sig')  # utf-8-sig for Excel compatibility
    return csv
def create_printable_timetable(schedule_df, entity_type=None, selected_entity=None):
    """Create a printable HTML version of the timetable."""
    if schedule_df is None or schedule_df.empty:
        return "<p>No schedule data available.</p>"
    
    # Create timetable grid
    timetable = create_timetable_grid(schedule_df, entity_type, selected_entity)
    
    # Convert to HTML with print-friendly styling
    html = f"""
    <html>
    <head>
        <title>Class Schedule - {selected_entity if selected_entity else 'All'}</title>
        <style>
            @page {{ size: landscape; margin: 0.5in; }}
            body {{ font-family: Arial, sans-serif; }}
            h1, h2 {{ text-align: center; color: #2E86AB; }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 20px;
                font-size: 10pt;
            }}
            th, td {{ 
                border: 1px solid #333; 
                padding: 8px; 
                text-align: center;
                vertical-align: top;
            }}
            th {{ 
                background-color: #2E86AB; 
                color: white; 
                font-weight: bold;
            }}
            td:first-child {{ 
                background-color: #f0f0f0; 
                font-weight: bold;
            }}
            .header-info {{
                text-align: center;
                margin-bottom: 20px;
            }}
            @media print {{
                body {{ margin: 0; }}
                table {{ page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <div class="header-info">
            <h1>Don Honorio Ventura State University</h1>
            <h2>College of Business Administration</h2>
            <h3>Class Schedule - {entity_type}: {selected_entity if selected_entity else 'All'}</h3>
            <p>Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
    """
    
    # Convert timetable DataFrame to HTML
    html += timetable.to_html(escape=False, index=True, index_names=False)
    html += """
    </body>
    </html>
    """
    
    return html

def clear_uploaded_files():
    """Clear all uploaded file references from session state."""
    file_keys = ['sections_upload_main', 'instructors_upload_main', 
                 'subjects_upload_main', 'rooms_upload_main', 'curriculum_upload_main']
    
    for key in file_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Reset data loaded flags
    st.session_state.data_loaded_flags = {
        'sections': False, 'instructors_raw': False, 'subjects': False, 
        'rooms_raw': False, 'curriculum': False
    }
    
    # Clear dataframes
    df_keys = ['sections_df', 'instructors_raw_df', 'subjects_df', 
               'rooms_raw_df', 'curriculum_df', 'parsed_instructors', 
               'parsed_rooms', 'classes_to_be_scheduled']
    
    for key in df_keys:
        if key in st.session_state:
            st.session_state[key] = None

def load_all_data_from_session_uploads():
    """Load all data from uploaded files."""
    # Sections
    sections_file_obj = st.session_state.get('sections_upload_main')
    if sections_file_obj is not None and st.session_state.sections_df is None:
        try:
            df = pd.read_csv(sections_file_obj)
            st.session_state.sections_df = df
            st.session_state.data_loaded_flags['sections'] = True
            st.success("✅ Sections data loaded!")
        except Exception as e:
            st.error(f"❌ Error loading Sections: {e}")
            st.session_state.data_loaded_flags['sections'] = False
    
    # Instructors
    instructors_file_obj = st.session_state.get('instructors_upload_main')
    if instructors_file_obj is not None and st.session_state.instructors_raw_df is None:
        try:
            df = pd.read_csv(instructors_file_obj)
            st.session_state.instructors_raw_df = df
            st.session_state.data_loaded_flags['instructors_raw'] = True
            st.success("✅ Instructor data loaded!")
        except Exception as e:
            st.error(f"❌ Error loading Instructors: {e}")
            st.session_state.data_loaded_flags['instructors_raw'] = False
    
    # Subjects
    subjects_file_obj = st.session_state.get('subjects_upload_main')
    if subjects_file_obj is not None and st.session_state.subjects_df is None:
        try:
            df = pd.read_csv(subjects_file_obj)
            st.session_state.subjects_df = df
            st.session_state.data_loaded_flags['subjects'] = True
            st.success("✅ Subjects data loaded!")
        except Exception as e:
            st.error(f"❌ Error loading Subjects: {e}")
            st.session_state.data_loaded_flags['subjects'] = False
    
    # Rooms
    rooms_file_obj = st.session_state.get('rooms_upload_main')
    if rooms_file_obj is not None and st.session_state.rooms_raw_df is None:
        try:
            df = pd.read_csv(rooms_file_obj)
            st.session_state.rooms_raw_df = df
            st.session_state.data_loaded_flags['rooms_raw'] = True
            st.success("✅ Rooms data loaded!")
        except Exception as e:
            st.error(f"❌ Error loading Rooms: {e}")
            st.session_state.data_loaded_flags['rooms_raw'] = False
    
    # Curriculum
    curriculum_file_obj = st.session_state.get('curriculum_upload_main')
    if curriculum_file_obj is not None and st.session_state.curriculum_df is None:
        try:
            df = pd.read_csv(curriculum_file_obj)
            st.session_state.curriculum_df = df
            st.session_state.data_loaded_flags['curriculum'] = True
            st.success("✅ Curriculum mapping loaded!")
        except Exception as e:
            st.error(f"❌ Error loading Curriculum: {e}")
            st.session_state.data_loaded_flags['curriculum'] = False

def create_timetable_grid(schedule_df, entity_type=None, selected_entity=None):
    """Create a timetable grid from schedule data with color coding."""
    if schedule_df is None or schedule_df.empty:
        return pd.DataFrame(index=TIME_SLOTS_DISPLAY, columns=DAYS_ORDER).fillna('')

    schedule_df['Day'] = schedule_df['Day'].str.upper()

    filtered_schedule = schedule_df.copy()
    if entity_type and selected_entity and selected_entity != "All":
        if entity_type == "Room" and "Room" in filtered_schedule.columns:
            filtered_schedule = filtered_schedule[filtered_schedule['Room'] == selected_entity]
        elif entity_type == "Section" and "Section" in filtered_schedule.columns:
            filtered_schedule = filtered_schedule[filtered_schedule['Section'] == selected_entity]
        elif entity_type == "Instructor" and "Instructor" in filtered_schedule.columns:
            filtered_schedule = filtered_schedule[filtered_schedule['Instructor'] == selected_entity]
    
    if filtered_schedule.empty and selected_entity != "All":
        return pd.DataFrame(index=TIME_SLOTS_DISPLAY, columns=DAYS_ORDER).fillna('')

    timetable = pd.DataFrame(index=TIME_SLOTS_DISPLAY, columns=DAYS_ORDER)
    timetable = timetable.fillna('') 

    # Get all unique subject codes for consistent color assignment
    all_subject_codes = sorted(schedule_df['Subject Code'].unique().tolist())

    for _, row in filtered_schedule.iterrows():
        day = row['Day']
        time_slot_24hr_data = row['Time Slot']
        
        display_time_slot_for_index = format_time_slot_for_display(time_slot_24hr_data)
        
        # Get color for this subject
        subject_code = row.get('Subject Code', 'N/A')
        color = get_color_for_subject(subject_code, all_subject_codes)
        
        # Create cell content with color styling
        cell_content = f'<div style="background-color: {color}; color: white; padding: 8px; border-radius: 5px; font-weight: 500; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">'
        cell_content += f'<strong>{subject_code}</strong>'
        
        if entity_type == "Room": 
            cell_content += f"<br>Sec: {row.get('Section', 'N/A')}<br>Prof: {row.get('Instructor', 'N/A')[:30]}" 
        elif entity_type == "Section": 
            cell_content += f"<br>Room: {row.get('Room', 'N/A')}<br>Prof: {row.get('Instructor', 'N/A')[:30]}"
        elif entity_type == "Instructor": 
            cell_content += f"<br>Room: {row.get('Room', 'N/A')}<br>Sec: {row.get('Section', 'N/A')}"
        else: 
            cell_content += f"<br>{row.get('Section', 'N/A')}<br>{row.get('Instructor', 'N/A')[:30]}<br>{row.get('Room', 'N/A')}"
        
        cell_content += '</div>'

        if day in timetable.columns and display_time_slot_for_index in timetable.index:
            if timetable.loc[display_time_slot_for_index, day] == '':
                timetable.loc[display_time_slot_for_index, day] = cell_content
            else:
                timetable.loc[display_time_slot_for_index, day] += f'<div style="margin-top: 4px;">{cell_content}</div>'

    return timetable

# --- Session State Initialization ---
if 'data_loaded_flags' not in st.session_state:
    st.session_state.data_loaded_flags = {
        'sections': False, 'instructors_raw': False, 'subjects': False, 
        'rooms_raw': False, 'curriculum': False
    }
if 'sections_df' not in st.session_state: st.session_state.sections_df = None
if 'instructors_raw_df' not in st.session_state: st.session_state.instructors_raw_df = None
if 'subjects_df' not in st.session_state: st.session_state.subjects_df = None
if 'rooms_raw_df' not in st.session_state: st.session_state.rooms_raw_df = None
if 'curriculum_df' not in st.session_state: st.session_state.curriculum_df = None
if 'parsed_instructors' not in st.session_state: st.session_state.parsed_instructors = None
if 'parsed_rooms' not in st.session_state: st.session_state.parsed_rooms = None
if 'classes_to_be_scheduled' not in st.session_state: st.session_state.classes_to_be_scheduled = None
if 'generated_schedule_df' not in st.session_state: st.session_state.generated_schedule_df = None
if 'conflicts' not in st.session_state: st.session_state.conflicts = []

# --- Main App Title with Modern Hero Section ---
st.markdown("""
<div class="hero-section">
    <h1 style="margin: 0; font-size: 2.5rem;">📅 Honorians InSync</h1>
    <p style="font-size: 1.2rem; margin-top: 0.5rem;">Automated Resource and Scheduling Management System</p>
</div>
""", unsafe_allow_html=True)

# --- Define Tabs ---
tab_about, tab_upload, tab_run, tab_schedule, tab_conflicts = st.tabs([
    "🏠 About & Workflow",
    "📤 Upload & Verify Data", 
    "🚀 Run Scheduler", 
    "📅 View Schedule", 
    "⚠️ Resolve Conflicts"
])

# --- Tab 0: Workflow & About ---
with tab_about:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(
            "https://dhvsu.edu.ph/images/DHVSU-LOGO.png",
            caption="Don Honorio Ventura State University",
            use_container_width=True,
        )
    with col2:
        st.markdown("""
        ### Automated Scheduling System
        
        **Honorians InSync** is a state-of-the-art web-based Automated Scheduling & Resource Management System 
        designed to revolutionize course scheduling and room resource management at the College of Business 
        Administration, DHVSU.
        
        This system employs advanced algorithms to optimize class schedules while considering multiple constraints 
        including teacher availability, room capacity, and subject specializations.
        """)
    
    st.divider()

    # Workflow Section with Cards
    st.subheader("📋 System Workflow")
    
    workflow_cols = st.columns(4)
    workflow_steps = [
        ("1️⃣", "Upload & Verify", "Upload CSV files containing sections, instructors, subjects, rooms, and curriculum data.", "#2E86AB"),
        ("2️⃣", "Run Scheduler", "Click Generate to let our intelligent algorithm build an optimized timetable.", "#A23B72"),
        ("3️⃣", "View Schedule", "Filter and explore the generated schedule by room, section, or instructor.", "#27AE60"),
        ("4️⃣", "Resolve Conflicts", "Interactively fix any unscheduled classes or scheduling conflicts.", "#F39C12"),
    ]
    
    for col, (emoji, title, description, color) in zip(workflow_cols, workflow_steps):
        with col:
            st.markdown(f"""
            <div class="workflow-card">
                <h4 style="color: {color};">{emoji} {title}</h4>
                <p style="font-size: 0.9rem;">{description}</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Key Features
    st.subheader("🔑 Key Features")
    
    feature_cols = st.columns(3)
    
    with feature_cols[0]:
        st.markdown("""
        #### 🤖 Intelligent Scheduling
        - Advanced conflict detection
        - Teacher specialization matching
        - Capacity optimization
        - Section clash prevention
        """)
    
    with feature_cols[1]:
        st.markdown("""
        #### 📊 Interactive Dashboard
        - Real-time schedule visualization
        - Multiple filtering options
        - Print-ready formats
        - CSV export capability
        """)
    
    with feature_cols[2]:
        st.markdown("""
        #### 🔧 Conflict Resolution
        - Manual override options
        - Force assignment capability
        - Double booking detection
        - Detailed conflict reporting
        """)

    st.divider()

    # Data Blueprint
    st.subheader("📂 Data Requirements")
    st.markdown("Upload CSV files with the following headers:")
    
    data_cols = st.columns(5)
    
    with data_cols[0]:
        st.markdown("""
        <div class="data-blueprint-item">
            <p class="item-label">📝 Sections Data</p>
            <p class="item-headers">Course, Year Level, Section, Students</p>
        </div>
        """, unsafe_allow_html=True)

    with data_cols[1]:
        st.markdown("""
        <div class="data-blueprint-item">
            <p class="item-label">🧑‍🏫 Instructor Data</p>
            <p class="item-headers">Instructor, Day, Time Slot, Department, Specialization</p>
        </div>
        """, unsafe_allow_html=True)

    with data_cols[2]:
        st.markdown("""
        <div class="data-blueprint-item">
            <p class="item-label">📚 Subjects Data</p>
            <p class="item-headers">Subject Code, Subject Name, Required Specialization</p>
        </div>
        """, unsafe_allow_html=True)

    with data_cols[3]:
        st.markdown("""
        <div class="data-blueprint-item">
            <p class="item-label">🏫 Rooms Data</p>
            <p class="item-headers">Room, Day, Time Slot, Max Capacity</p>
        </div>
        """, unsafe_allow_html=True)

    with data_cols[4]:
        st.markdown("""
        <div class="data-blueprint-item">
            <p class="item-label">🗺️ Curriculum</p>
            <p class="item-headers">Course, Year Level, Subject Code</p>
        </div>
        """, unsafe_allow_html=True)

# --- Tab 1: Upload & Verify Data ---
with tab_upload:
    st.header("📤 Upload Data Files")
    
    # File Upload Section with improved layout
    upload_cols = st.columns(2)
    
    with upload_cols[0]:
        st.markdown("### Core Data Files")
        st.file_uploader("📝 Sections Data", type="csv", key="sections_upload_main", help="Upload sections CSV file")
        st.file_uploader("🧑‍🏫 Instructor Data", type="csv", key="instructors_upload_main", help="Upload instructors CSV file")
        st.file_uploader("📚 Subjects Data", type="csv", key="subjects_upload_main", help="Upload subjects CSV file")
    
    with upload_cols[1]:
        st.markdown("### Resource & Mapping Files")
        st.file_uploader("🏫 Rooms Data", type="csv", key="rooms_upload_main", help="Upload rooms CSV file")
        st.file_uploader("🗺️ Curriculum Mapping", type="csv", key="curriculum_upload_main", help="Upload curriculum CSV file")

    # Load data button
    if st.button("🔄 Load All Uploaded Files", type="primary", use_container_width=True):
        load_all_data_from_session_uploads()
        
        # Process data if loaded
        if st.session_state.data_loaded_flags.get('instructors_raw', False) and \
           st.session_state.instructors_raw_df is not None and \
           st.session_state.parsed_instructors is None:
            st.session_state.parsed_instructors = process_instructor_data(st.session_state.instructors_raw_df)
            if st.session_state.parsed_instructors is not None: 
                st.info("✅ Instructor data processed successfully!")

        if st.session_state.data_loaded_flags.get('rooms_raw', False) and \
           st.session_state.rooms_raw_df is not None and \
           st.session_state.parsed_rooms is None:
            st.session_state.parsed_rooms = process_room_data(st.session_state.rooms_raw_df)
            if st.session_state.parsed_rooms is not None: 
                st.info("✅ Room data processed successfully!")
        
        # Generate list of classes
        all_input_dfs_for_class_list_loaded = (
            st.session_state.sections_df is not None and
            st.session_state.subjects_df is not None and
            st.session_state.curriculum_df is not None
        )
        if all_input_dfs_for_class_list_loaded and st.session_state.classes_to_be_scheduled is None:
            st.session_state.classes_to_be_scheduled = get_classes_to_schedule(
                st.session_state.sections_df, st.session_state.subjects_df, st.session_state.curriculum_df
            )
            if st.session_state.classes_to_be_scheduled: 
                st.success(f"✅ {len(st.session_state.classes_to_be_scheduled)} class instances identified and ready for scheduling!")

    st.markdown("---")
    
    # Data Verification Section
    st.header("🔍 Data Verification")
    
    verification_cols = st.columns(3)
    
    with verification_cols[0]:
        if st.session_state.sections_df is not None:
            with st.expander("📝 Sections Data Preview", expanded=False):
                st.dataframe(st.session_state.sections_df.head(), use_container_width=True)
                st.caption(f"Total sections: {len(st.session_state.sections_df)}")
    
    with verification_cols[1]:
        if st.session_state.instructors_raw_df is not None:
            with st.expander("🧑‍🏫 Instructors Data Preview", expanded=False):
                st.dataframe(st.session_state.instructors_raw_df.head(), use_container_width=True)
                if st.session_state.parsed_instructors:
                    st.caption(f"Total unique instructors: {len(st.session_state.parsed_instructors)}")
    
    with verification_cols[2]:
        if st.session_state.subjects_df is not None:
            with st.expander("📚 Subjects Data Preview", expanded=False):
                st.dataframe(st.session_state.subjects_df.head(), use_container_width=True)
                st.caption(f"Total subjects: {len(st.session_state.subjects_df)}")
    
    # Second row
    verification_cols2 = st.columns(2)
    
    with verification_cols2[0]:
        if st.session_state.rooms_raw_df is not None:
            with st.expander("🏫 Rooms Data Preview", expanded=False):
                st.dataframe(st.session_state.rooms_raw_df.head(), use_container_width=True)
                if st.session_state.parsed_rooms:
                    st.caption(f"Total unique rooms: {len(st.session_state.parsed_rooms)}")
    
    with verification_cols2[1]:
        if st.session_state.curriculum_df is not None:
            with st.expander("🗺️ Curriculum Mapping Preview", expanded=False):
                st.dataframe(st.session_state.curriculum_df.head(), use_container_width=True)
                st.caption(f"Total curriculum entries: {len(st.session_state.curriculum_df)}")

# --- Tab 2: Run Scheduler ---
with tab_run:
    st.header("🚀 Run the Automated Scheduler")
    
    ready_to_schedule_check = (
        st.session_state.classes_to_be_scheduled and 
        st.session_state.parsed_instructors and 
        st.session_state.parsed_rooms
    )

    if not ready_to_schedule_check:
        st.warning("⚠️ Please ensure all data is uploaded and processed in the Upload tab before running the scheduler.")
    else:
        st.success(f"✅ Ready to schedule {len(st.session_state.classes_to_be_scheduled)} class instances!")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🎯 Generate Class Schedule", 
                     disabled=not ready_to_schedule_check, 
                     type="primary", 
                     use_container_width=True):
            
            with st.spinner("🔄 Generating optimal schedule... This may take a moment."):
                schedule_result, conflicts_result = generate_schedule_attempt(
                    st.session_state.classes_to_be_scheduled,
                    st.session_state.parsed_instructors,
                    st.session_state.parsed_rooms
                )
            
            st.session_state.generated_schedule_df = pd.DataFrame(schedule_result)
            st.session_state.conflicts = conflicts_result
            
            # Clear uploaded files after successful generation
            clear_uploaded_files()
            
            if st.session_state.generated_schedule_df is not None and not st.session_state.generated_schedule_df.empty:
                st.balloons()
                st.success(f"✅ Schedule generation complete! {len(st.session_state.generated_schedule_df)} classes successfully scheduled.")
                
                # Show summary statistics
                summary_cols = st.columns(4)
                with summary_cols[0]:
                    st.metric("Total Classes Scheduled", len(st.session_state.generated_schedule_df))
                with summary_cols[1]:
                    st.metric("Conflicts Found", len(st.session_state.conflicts))
                with summary_cols[2]:
                    if st.session_state.get('classes_to_be_scheduled') and len(st.session_state.classes_to_be_scheduled) > 0:
                        success_rate = (len(st.session_state.generated_schedule_df) / len(st.session_state.classes_to_be_scheduled) * 100)
                        st.metric("Success Rate", f"{success_rate:.1f}%")
                    else:
                        st.metric("Success Rate", "N/A")
                with summary_cols[3]:
                    st.metric("Unscheduled Classes", len([c for c in st.session_state.conflicts if c['type'] == 'Unscheduled Class']))
                
                st.info("📄 Uploaded files have been cleared. You can now view and export the generated schedule.")
            else:
                st.error("❌ No classes could be scheduled. Please check your input data and try again.")

# --- Tab 3: View Generated Schedule ---
# In Tab 3, replace the export section with this:
with tab_schedule:
    st.header("📅 Generated Class Schedule")

    if st.session_state.generated_schedule_df is not None and not st.session_state.generated_schedule_df.empty:
        
        # Export Options
        export_cols = st.columns([2, 1, 1])
        
        with export_cols[0]:
            st.markdown("### 📤 Export Options")
                    # Get current filter settings
                    
        current_filter_type = st.session_state.get('timetable_filter_type', 'Overall View')
        current_entity = 'All'
        
        if current_filter_type != 'Overall View':
            current_entity = st.session_state.get(f'timetable_select_{current_filter_type.lower()}', 'All')
        
        with export_cols[1]:
            # CSV Export - Filtered version
            # Apply same filtering as the display
            filtered_df = st.session_state.generated_schedule_df.copy()
            
            if current_filter_type != "Overall View" and current_entity != "All":
                if current_filter_type == "Room":
                    filtered_df = filtered_df[filtered_df['Room'] == current_entity]
                elif current_filter_type == "Section":
                    filtered_df = filtered_df[filtered_df['Section'] == current_entity]
                elif current_filter_type == "Instructor":
                    filtered_df = filtered_df[filtered_df['Instructor'] == current_entity]
            
            csv = export_schedule_to_csv(filtered_df)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
                        # Create filename with filter info
            filter_suffix = ""
            if current_filter_type != "Overall View" and current_entity != "All":
                filter_suffix = f"_{current_filter_type}_{current_entity.replace(' ', '_')}"
            
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"schedule{filter_suffix}_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with export_cols[2]:
            # Export filtered timetable
            if st.button("🖨️ Export for Print", use_container_width=True):
                # Get the current timetable grid (already filtered)
                timetable_grid = create_timetable_grid(
                    st.session_state.generated_schedule_df,
                    current_filter_type if current_filter_type != "Overall View" else None,
                    current_entity if current_entity != "All" else None
                )
                
                # Convert timetable grid to a more print-friendly format
                # Remove HTML tags for CSV export
                print_timetable = timetable_grid.copy()
                
                # Clean HTML from cells
                for col in print_timetable.columns:
                    print_timetable[col] = print_timetable[col].apply(
                        lambda x: clean_html_for_export(x) if x else ''
                    )
                
                # Add metadata header
                metadata_rows = []
                metadata_rows.append(['DHVSU Class Schedule'])
                metadata_rows.append([f'Generated on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}'])
                
                if current_filter_type != "Overall View" and current_entity != "All":
                    metadata_rows.append([f'{current_filter_type}: {current_entity}'])
                else:
                    metadata_rows.append(['Schedule Type: Complete Schedule'])
                
                metadata_rows.append([''])  # Empty row for spacing
                
                # Convert metadata to DataFrame
                metadata_df = pd.DataFrame(metadata_rows)
                
                # Combine metadata with timetable
                # First, convert timetable to include its index as a column
                export_timetable = print_timetable.reset_index()
                export_timetable.rename(columns={'index': 'Time Slot'}, inplace=True)
                
                # Create the final CSV content
                csv_content = metadata_df.to_csv(index=False, header=False)
                csv_content += export_timetable.to_csv(index=False)
                
                # Create filename with filter info
                export_filename = f"timetable{filter_suffix}_{timestamp}.csv"
                
                st.download_button(
                    label="📄 Download Timetable",
                    data=csv_content,
                    file_name=export_filename,
                    mime="text/csv",
                    use_container_width=True,
                    key="print_timetable_download"
                )
                
                st.success(f"✅ Timetable exported! {'Filtered by ' + current_filter_type + ': ' + current_entity if current_entity != 'All' else 'Complete schedule'}")
        
        # Add export information
        if current_filter_type != "Overall View" and current_entity != "All":
            st.info(f"📌 **Export Info:** Currently viewing and exporting schedule for {current_filter_type}: **{current_entity}**")
        else:
            st.info("📌 **Export Info:** Currently viewing and exporting the complete schedule")
        
        # Filter Options in Sidebar
        st.sidebar.markdown("### 🔍 Schedule Filters")
        
        filter_type_options = ["Overall View", "Room", "Section", "Instructor"]
        selected_filter_type = st.sidebar.selectbox(
            "Filter by:", 
            filter_type_options, 
            key="timetable_filter_type"
        )

        entity_list = ["All"]
        selected_entity = "All"

        if selected_filter_type == "Room":
            if "Room" in st.session_state.generated_schedule_df.columns:
                entity_list.extend(sorted(st.session_state.generated_schedule_df['Room'].unique().tolist()))
        elif selected_filter_type == "Section":
            if "Section" in st.session_state.generated_schedule_df.columns:
                entity_list.extend(sorted(st.session_state.generated_schedule_df['Section'].unique().tolist()))
        elif selected_filter_type == "Instructor":
            if "Instructor" in st.session_state.generated_schedule_df.columns:
                entity_list.extend(sorted(st.session_state.generated_schedule_df['Instructor'].unique().tolist()))
        
        if selected_filter_type != "Overall View":
            selected_entity = st.sidebar.selectbox(
                f"Select {selected_filter_type}:", 
                entity_list, 
                key=f"timetable_select_{selected_filter_type.lower()}"
            )

        # Display Schedule
        schedule_to_display = st.session_state.generated_schedule_df.copy()
        
        if 'Day' in schedule_to_display.columns:
            schedule_to_display['Day'] = schedule_to_display['Day'].astype(str).str.upper()

        if selected_filter_type == "Overall View":
            st.subheader("📋 Master Schedule Overview")
            timetable_grid_df = create_timetable_grid(schedule_to_display, None, None)
        elif selected_entity and selected_entity != "All":
            st.subheader(f"📅 Schedule for {selected_filter_type}: **{selected_entity}**")
            timetable_grid_df = create_timetable_grid(schedule_to_display, selected_filter_type, selected_entity)
        else:
            st.info(f"Displaying combined schedule for all {selected_filter_type}s.")
            timetable_grid_df = create_timetable_grid(schedule_to_display, None, None)

        if not timetable_grid_df.empty:
            html_table = timetable_grid_df.to_html(
                escape=False,
                na_rep="",
                classes="schedule_table",
                index=True,
                index_names=False,
                border=0
            )

            enhanced_table_css = """
            <style>
                /* 1️⃣  --- container that locks the overall size --- */
                .timetable_box {
                    width: 900px;      /*  ⬅️  pick any width  */
                    height: 520px;     /*  ⬅️  pick any height */
                    overflow: auto;    /*  scrollbars when content overflows */
                    margin: 0 auto;    /*  center horizontally (optional) */
                }

                /* 2️⃣  --- fix the table geometry --- */
                table.schedule_table {
                    table-layout: fixed;   /* cells obey the width rule below   */
                    width: 100%;           /* stretches to the .timetable_box   */
                    height: 100%;          /* ditto                              */
                    border-collapse: collapse;
                    background: #fff;
                    border-radius: 10px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }

                /* 3️⃣  --- cap individual cell sizes --- */
                table.schedule_table th,
                table.schedule_table td {
                    width: 120px;      /*  fixed column width    */
                    height: 80px;      /*  fixed row height      */
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    border: 1px solid #e0e0e0;
                    padding: 8px;
                    text-align: center;
                    vertical-align: middle;
                    font-size: 0.85em;
                }

                /* existing colours & sticky headers … */
                table.schedule_table th {
                    background: #2E86AB; color: #fff; font-weight: 600;
                    text-transform: uppercase; letter-spacing: 0.5px;
                    position: sticky; top: 0; z-index: 10;
                }

                table.schedule_table td:first-child {
                    background: #f8f9fa; color: #2E86AB; font-weight: 600;
                    position: sticky; left: 0; z-index: 5;
                }

                table.schedule_table td { background: #fafafa; transition: background 0.3s; }
                table.schedule_table td:hover { background: #f0f0f0; }
            </style>
            """
            
            st.markdown(enhanced_table_css, unsafe_allow_html=True)
            st.markdown(html_table, unsafe_allow_html=True)
            
            # Display raw data option
            with st.expander("📊 View Raw Schedule Data"):
                st.dataframe(
                    st.session_state.generated_schedule_df,
                    use_container_width=True,
                    height=400
                )
        else:
            st.info("No schedule data to display for the selected filter.")
    else:
        st.info("🔄 No schedule has been generated yet. Please run the scheduler first.")

# --- Tab 4: Resolve Conflicts ---
with tab_conflicts:
    st.header("⚠️ Resolve Scheduling Conflicts")

    # Initialize conflict resolution session states
    if 'selected_conflict_to_resolve_idx' not in st.session_state:
        st.session_state.selected_conflict_to_resolve_idx = None
    if 'selected_conflict_type' not in st.session_state:
        st.session_state.selected_conflict_type = None
    if 'manual_assignment_feedback' not in st.session_state:
        st.session_state.manual_assignment_feedback = None
    if 'class_to_modify_from_double_booking_idx' not in st.session_state:
        st.session_state.class_to_modify_from_double_booking_idx = None

    if st.session_state.conflicts:
        # Summary metrics
        conflict_cols = st.columns(4)
        
        unscheduled_count = len([c for c in st.session_state.conflicts if c['type'] == 'Unscheduled Class'])
        double_booking_count = len([c for c in st.session_state.conflicts if 'Double' in c['type']])
        
        with conflict_cols[0]:
            st.metric("Total Conflicts", len(st.session_state.conflicts))
        with conflict_cols[1]:
            st.metric("Unscheduled Classes", unscheduled_count)
        with conflict_cols[2]:
            st.metric("Double Bookings", double_booking_count)
        with conflict_cols[3]:
            st.metric("Other Issues", len(st.session_state.conflicts) - unscheduled_count - double_booking_count)
        
        st.markdown("---")
        
        # Conflict Overview
        st.subheader("📋 Conflict Overview")
        conflicts_df_display = pd.DataFrame(st.session_state.conflicts)
        st.dataframe(conflicts_df_display, use_container_width=True, height=200)
        
        st.markdown("---")

        # Conflict Resolution Section
        st.subheader("🔧 Select a Conflict to Resolve")

        conflict_options = ["Select a conflict..."]
        resolvable_conflict_details = []

        for idx, c in enumerate(st.session_state.conflicts):
            display_str = f"#{idx}: {c['type']} - "
            if c['type'] == 'Unscheduled Class':
                display_str += f"Section: {c.get('section', 'N/A')}, Subject: {c.get('subject', 'N/A')}"
                conflict_options.append(display_str)
                resolvable_conflict_details.append({'display': display_str, 'original_index': idx, 'type': c['type']})
            elif 'Double Book' in c.get('type', ''):
                if 'Teacher Double Book' in c['type']:
                    display_str += f"Teacher: {c.get('instructor', 'N/A')} at {c.get('day','N/A')} {c.get('time_slot','N/A')}"
                elif 'Room Double Book' in c['type']:
                    display_str += f"Room: {c.get('room', 'N/A')} at {c.get('day','N/A')} {c.get('time_slot','N/A')}"
                conflict_options.append(display_str)
                resolvable_conflict_details.append({'display': display_str, 'original_index': idx, 'type': c['type']})

        selected_conflict_display_str_main = st.selectbox(
            "Choose a conflict to resolve:",
            conflict_options,
            key="main_conflict_selector_tab4"
        )

        # Update session state for selected conflict
        if selected_conflict_display_str_main != "Select a conflict...":
            for item in resolvable_conflict_details:
                if item['display'] == selected_conflict_display_str_main:
                    st.session_state.selected_conflict_to_resolve_idx = item['original_index']
                    st.session_state.selected_conflict_type = item['type']
                    if 'Double Book' not in item['type']:
                        st.session_state.class_to_modify_from_double_booking_idx = None
                    break
        else:
            st.session_state.selected_conflict_to_resolve_idx = None
            st.session_state.selected_conflict_type = None
            st.session_state.manual_assignment_feedback = None
            st.session_state.class_to_modify_from_double_booking_idx = None

        # Display Resolution Form based on Selected Conflict Type
        if st.session_state.selected_conflict_to_resolve_idx is not None:
            conflict_original_idx = st.session_state.selected_conflict_to_resolve_idx
            
            if not (0 <= conflict_original_idx < len(st.session_state.conflicts)):
                st.warning("Selected conflict is no longer valid. Please re-select.")
                st.session_state.selected_conflict_to_resolve_idx = None
                st.session_state.selected_conflict_type = None
            else:
                conflict_to_resolve = st.session_state.conflicts[conflict_original_idx]
                
                st.markdown("---")
                
                # --- A. Resolver for "Unscheduled Class" ---
                if st.session_state.selected_conflict_type == 'Unscheduled Class':
                    st.markdown(f"""
                    <div class="conflict-card">
                        <h4>🔴 Unscheduled Class Details</h4>
                        <p><strong>Section:</strong> {conflict_to_resolve['section']}</p>
                        <p><strong>Subject:</strong> {conflict_to_resolve['subject']}</p>
                        <p><strong>Students:</strong> {conflict_to_resolve['students']}</p>
                        <p><strong>Required Specialization:</strong> {conflict_to_resolve['required_specialization']}</p>
                        <p><strong>Reason:</strong> {conflict_to_resolve['reason']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.form(key=f"unscheduled_form_{conflict_original_idx}"):
                        st.markdown("### 📝 Manual Assignment")
                        
                        form_cols = st.columns(2)
                        
                        with form_cols[0]:
                            # Teacher selection
                            sel_teacher_options = ["Select..."]
                            if st.session_state.get('parsed_instructors'):
                                sel_teacher_options.extend(sorted([
                                    name for name, details in st.session_state['parsed_instructors'].items()
                                    if conflict_to_resolve['required_specialization'] in details['specializations']
                                ]))
                            selected_teacher = st.selectbox("Select Teacher:", sel_teacher_options, key=f"uns_teacher_{conflict_original_idx}")
                            
                            # Day selection
                            selected_day = st.selectbox("Select Day:", ["Select..."] + DAYS_ORDER, key=f"uns_day_{conflict_original_idx}")
                        
                        with form_cols[1]:
                            # Room selection
                            sel_room_options = ["Select..."]
                            if st.session_state.get('parsed_rooms'):
                                sel_room_options.extend(sorted([
                                    name for name, room_slots in st.session_state['parsed_rooms'].items()
                                    if any(details['capacity'] >= conflict_to_resolve['students'] 
                                          for details in room_slots.values())
                                ]))
                            selected_room = st.selectbox("Select Room:", sel_room_options, key=f"uns_room_{conflict_original_idx}")
                            
                            # Time slot selection
                            selected_time_slot = st.selectbox("Select Time Slot:", ["Select..."] + TIME_SLOTS_ORDER_24HR, key=f"uns_time_{conflict_original_idx}")
                        
                        st.warning("⚠️ Force assignment will override all constraints and may create new conflicts. Use with caution!")
                        
                        submitted_unscheduled_fix = st.form_submit_button("🔧 Force Assign Class", type="primary", use_container_width=True)
                        
                        if submitted_unscheduled_fix:
                            st.session_state.manual_assignment_feedback = None
                            
                            if selected_teacher == "Select..." or selected_room == "Select..." or \
                               selected_day == "Select..." or selected_time_slot == "Select...":
                                st.error("❌ Please make complete selections for all fields.")
                            else:
                                # Get additional details
                                subject_name_val = 'N/A'
                                if st.session_state.get('subjects_df') is not None:
                                    subj_series = st.session_state['subjects_df'][
                                        st.session_state['subjects_df']['Subject Code'] == conflict_to_resolve['subject']
                                    ]['Subject Name']
                                    if not subj_series.empty:
                                        subject_name_val = subj_series.iloc[0]
                                
                                room_capacity_val = 'N/A'
                                if st.session_state.get('parsed_rooms') and \
                                   selected_room in st.session_state['parsed_rooms'] and \
                                   (selected_day.upper(), selected_time_slot) in st.session_state['parsed_rooms'][selected_room]:
                                    room_capacity_val = st.session_state['parsed_rooms'][selected_room][(selected_day.upper(), selected_time_slot)]['capacity']
                                
                                forced_class_details = {
                                    'Section': conflict_to_resolve['section'],
                                    'Subject Code': conflict_to_resolve['subject'],
                                    'Subject Name': subject_name_val,
                                    'Instructor': selected_teacher,
                                    'Room': selected_room,
                                    'Day': selected_day.upper(),
                                    'Time Slot': selected_time_slot,
                                    'Students': conflict_to_resolve['students'],
                                    'Room Capacity': room_capacity_val,
                                    'Assignment Type': 'Manual (Forced)'
                                }
                                
                                # Add to schedule
                                if st.session_state.get('generated_schedule_df') is None:
                                    st.session_state.generated_schedule_df = pd.DataFrame([forced_class_details])
                                else:
                                    new_row_df = pd.DataFrame([forced_class_details])
                                    st.session_state.generated_schedule_df = pd.concat(
                                        [st.session_state.generated_schedule_df, new_row_df], 
                                        ignore_index=True
                                    )
                                
                                # Remove conflict
                                st.session_state.conflicts.pop(conflict_original_idx)
                                
                                st.success(f"✅ Successfully force assigned {forced_class_details['Subject Code']} for {forced_class_details['Section']}!")
                                st.warning("⚠️ This assignment was forced and may have created new conflicts. Please review the schedule carefully.")
                                
                                # Clear selection and rerun
                                st.session_state.selected_conflict_to_resolve_idx = None
                                st.session_state.selected_conflict_type = None
                                st.rerun()

                # --- B. Resolver for "Teacher Double Booked" ---
                elif 'Teacher Double Book' in st.session_state.selected_conflict_type:
                    st.markdown(f"""
                    <div class="conflict-card">
                        <h4>🔴 Teacher Double Booking</h4>
                        <p><strong>Teacher:</strong> {conflict_to_resolve['instructor']}</p>
                        <p><strong>Day:</strong> {conflict_to_resolve['day']}</p>
                        <p><strong>Time:</strong> {conflict_to_resolve['time_slot']}</p>
                        <p><strong>Conflicting Classes:</strong> {conflict_to_resolve['classes_involved']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    conflicting_schedule_entries = []
                    if st.session_state.generated_schedule_df is not None:
                        # Ensure Day comparison is case-insensitive if necessary
                        # Assuming conflict_to_resolve['day'] is already uppercase from post-check
                        conflicting_schedule_entries = st.session_state.generated_schedule_df[
                            (st.session_state.generated_schedule_df['Instructor'] == conflict_to_resolve['instructor']) &
                            (st.session_state.generated_schedule_df['Day'].str.upper() == conflict_to_resolve['day']) & # Match Day case
                            (st.session_state.generated_schedule_df['Time Slot'] == conflict_to_resolve['time_slot'])
                        ].copy()
                        if not conflicting_schedule_entries.empty:
                             conflicting_schedule_entries['original_df_index'] = conflicting_schedule_entries.index
                    
                    if not conflicting_schedule_entries.empty:
                        st.markdown("### 🔄 Select a class to forcibly reschedule:")
                        
                        class_options_to_modify = ["Select a class..."] + \
                            [f"ID {row['original_df_index']}: {row['Subject Code']} for {row['Section']} in {row['Room']}" 
                             for _, row in conflicting_schedule_entries.iterrows()]
                        
                        selected_class_str_to_modify = st.selectbox(
                            "Choose class to forcibly move:", 
                            class_options_to_modify, 
                            key=f"tdb_class_select_force_{conflict_original_idx}" # New key for clarity
                        )

                        if selected_class_str_to_modify != "Select a class...":
                            try:
                                df_idx_to_modify = int(selected_class_str_to_modify.split(':')[0].replace('ID','').strip())
                                st.session_state.class_to_modify_from_double_booking_idx = df_idx_to_modify
                            except ValueError:
                                st.session_state.class_to_modify_from_double_booking_idx = None

                        if st.session_state.class_to_modify_from_double_booking_idx is not None and \
                           st.session_state.class_to_modify_from_double_booking_idx in st.session_state.generated_schedule_df.index: # Check if index still valid
                            
                            class_to_modify_details = st.session_state.generated_schedule_df.loc[
                                st.session_state.class_to_modify_from_double_booking_idx
                            ]
                            
                            st.markdown(f"#### 📝 Forcibly Modifying: {class_to_modify_details['Subject Code']} for Section {class_to_modify_details['Section']}")
                            
                            with st.form(key=f"tdb_force_resolve_form_{conflict_original_idx}_{st.session_state.class_to_modify_from_double_booking_idx}"):
                                st.write("**New Assignment** (This will be a forced assignment):")
                                
                                form_cols = st.columns(2)
                                
                                with form_cols[0]:
                                    # Teacher: Allow selecting ANY teacher
                                    all_teachers = ["Keep Original Teacher"] + sorted(list(st.session_state.parsed_instructors.keys())) if st.session_state.get('parsed_instructors') else ["Keep Original Teacher"]
                                    new_teacher = st.selectbox("New Teacher:", all_teachers, key=f"tdb_force_teacher_{conflict_original_idx}")
                                    
                                    new_day = st.selectbox("New Day:", ["Keep Original Day"] + DAYS_ORDER, key=f"tdb_force_day_{conflict_original_idx}")
                                
                                with form_cols[1]:
                                    # Room: Allow selecting ANY room
                                    all_rooms = ["Keep Original Room"] + sorted(list(st.session_state.parsed_rooms.keys())) if st.session_state.get('parsed_rooms') else ["Keep Original Room"]
                                    new_room = st.selectbox("New Room:", all_rooms, key=f"tdb_force_room_{conflict_original_idx}")
                                    
                                    # Use TIME_SLOTS_ORDER_24HR if that's your correct variable name, or TIME_SLOTS_ORDER
                                    new_time_slot = st.selectbox("New Time Slot:", ["Keep Original Time Slot"] + TIME_SLOTS_ORDER_24HR, key=f"tdb_force_time_{conflict_original_idx}") 
                                
                                st.warning("⚠️ This is a FORCE OVERRIDE. The selected class will be moved to the new teacher/room/slot regardless of existing schedules, specializations, or capacities. This may create new conflicts.")
                                submitted_tdb_force_fix = st.form_submit_button("💣 Force Reschedule This Class", type="primary", use_container_width=True)
                                
                                if submitted_tdb_force_fix:
                                    st.session_state.manual_assignment_feedback = None
                                    
                                    final_teacher = new_teacher if new_teacher != "Keep Original Teacher" else class_to_modify_details['Instructor']
                                    final_room = new_room if new_room != "Keep Original Room" else class_to_modify_details['Room']
                                    final_day = new_day.upper() if new_day != "Keep Original Day" else class_to_modify_details['Day'].upper() # Ensure Day is upper
                                    final_time_slot = new_time_slot if new_time_slot != "Keep Original Time Slot" else class_to_modify_details['Time Slot']
                                    
                                    if final_teacher == class_to_modify_details['Instructor'] and \
                                       final_room == class_to_modify_details['Room'] and \
                                       final_day == class_to_modify_details['Day'].upper() and \
                                       final_time_slot == class_to_modify_details['Time Slot']:
                                        st.warning("⚠️ No changes selected to force. Please choose new values if you intend to move the class.")
                                    else:
                                        # --- FORCE ASSIGNMENT LOGIC ---
                                        # No pre-checks for specialization or capacity here.
                                        # No call to check_manual_assignment_conflicts here.

                                        # Update the class details in the main schedule DataFrame
                                        idx_to_update = st.session_state.class_to_modify_from_double_booking_idx
                                        
                                        st.session_state.generated_schedule_df.loc[idx_to_update, 'Instructor'] = final_teacher
                                        st.session_state.generated_schedule_df.loc[idx_to_update, 'Room'] = final_room
                                        st.session_state.generated_schedule_df.loc[idx_to_update, 'Day'] = final_day
                                        st.session_state.generated_schedule_df.loc[idx_to_update, 'Time Slot'] = final_time_slot
                                        st.session_state.generated_schedule_df.loc[idx_to_update, 'Assignment Type'] = 'Manual (Forced TDB Fix)'
                                        # You might want to update 'Room Capacity' to reflect the new room if it changed, for display consistency
                                        if final_room != class_to_modify_details['Room'] and st.session_state.get('parsed_rooms') and \
                                           final_room in st.session_state['parsed_rooms'] and \
                                           (final_day, final_time_slot) in st.session_state['parsed_rooms'][final_room]:
                                            st.session_state.generated_schedule_df.loc[idx_to_update, 'Room Capacity'] = st.session_state['parsed_rooms'][final_room][(final_day, final_time_slot)]['capacity']
                                        elif final_room == class_to_modify_details['Room']:
                                            # Keep original capacity or re-fetch if time changed for same room
                                            pass 
                                        else:
                                            st.session_state.generated_schedule_df.loc[idx_to_update, 'Room Capacity'] = 'N/A (Forced)'


                                        # Remove the original "Teacher Double Booked" conflict
                                        # Important: Ensure conflict_original_idx is still valid for st.session_state.conflicts
                                        if 0 <= conflict_original_idx < len(st.session_state.conflicts):
                                            st.session_state.conflicts.pop(conflict_original_idx)
                                        else:
                                            st.warning("Could not remove original conflict from list (index out of bounds). List may need refreshing.")

                                        feedback_msg = (f"FORCE RESCHEDULED: {class_to_modify_details['Subject Code']} for Sec {class_to_modify_details['Section']}. "
                                                        f"New assignment: {final_teacher}, {final_room}, {final_day} {final_time_slot}.")
                                        st.warning(feedback_msg) # Warning for forced actions
                                        st.warning("This forced move may have created new conflicts. Review schedule carefully.")
                                        st.session_state.manual_assignment_feedback = feedback_msg
                                        
                                        st.session_state.selected_conflict_to_resolve_idx = None
                                        st.session_state.class_to_modify_from_double_booking_idx = None
                                        st.rerun()
                        # else part for if no class is selected to modify (selected_class_str_to_modify == "Select a class...")
                        # or if st.session_state.class_to_modify_from_double_booking_idx is None
                    else: # If conflicting_schedule_entries is empty (should not happen if TDB conflict exists)
                        st.error("Could not find the conflicting class entries in the current schedule. Data may be inconsistent.")

                # --- C. Resolver for "Room Double Booked" ---
                elif 'Room Double Book' in st.session_state.selected_conflict_type:
                    st.info("🚧 Room Double Booking resolution - Similar implementation to Teacher Double Booking")
                    # Implementation would follow the same pattern as Teacher Double Booking

        # Display last operation feedback
        if st.session_state.manual_assignment_feedback:
            st.info(f"Last operation: {st.session_state.manual_assignment_feedback}")

    elif st.session_state.generated_schedule_df is not None:
        st.success("✅ No conflicts detected! Your schedule is optimized and ready to use.")
        
        # Show success metrics
        success_cols = st.columns(3)
        with success_cols[0]:
            st.metric("Total Classes Scheduled", len(st.session_state.generated_schedule_df))
        with success_cols[1]:
            st.metric("Conflicts", 0, delta="All resolved!")
        with success_cols[2]:
            st.metric("Success Rate", "100%")
    else:
        st.info("🔄 No schedule has been generated yet. Please run the scheduler first in the 'Run Scheduler' tab.")
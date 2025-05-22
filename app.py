import streamlit as st
import pandas as pd
import copy 
from datetime import datetime


# --- Helper Function Definitions FIRST ---
# process_instructor_data, process_room_data, get_classes_to_schedule, generate_schedule_attempt
# (Assume these functions are defined here as before)
# Paste your existing functions here:

# Add these near the top of your app.py, or in a config section
DAYS_ORDER = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

TIME_SLOTS_ORDER_24HR = [
    "7:00-8:00", "8:00-9:00", "9:00-10:00", "10:00-11:00", 
    "11:00-12:00", "12:00-13:00", "13:00-14:00", "14:00-15:00", 
    "15:00-16:00", "16:00-17:00", "17:00-18:00"  #if your schedule extends later
]

def format_time_slot_for_display(time_slot_24hr):
    """Converts a 'HH:MM-HH:MM' 24-hour string to 'H:MM AM/PM - H:MM AM/PM' or 'H AM/PM - H AM/PM'."""
    try:
        start_str, end_str = time_slot_24hr.split('-')
        
        # Use strptime to parse and strftime to format
        # %I for 12-hour, %M for minute, %p for AM/PM
        # Using a dummy date because strptime needs a date part
        start_dt = datetime.strptime(start_str, "%H:%M")
        end_dt = datetime.strptime(end_str, "%H:%M")
        
        # Format without leading zero for hour if it's single digit (e.g., 7 AM instead of 07 AM)
        # and handle 12 PM/AM correctly.
        start_display = start_dt.strftime("%I:%M %p").lstrip('0').replace(" 00", " 12") # Handle 12 AM as 12:00 AM not 00:00 AM
        if start_display.startswith(":"): start_display = "12" + start_display # Correct 00:MM AM to 12:MM AM

        end_display = end_dt.strftime("%I:%M %p").lstrip('0').replace(" 00", " 12")
        if end_display.startswith(":"): end_display = "12" + end_display

        return f"{start_display} - {end_display}"
    except ValueError:
        # Fallback if the format is unexpected
        return time_slot_24hr

# Generate the display labels for the timetable rows
TIME_SLOTS_DISPLAY = [format_time_slot_for_display(ts) for ts in TIME_SLOTS_ORDER_24HR]

def check_manual_assignment_conflicts(schedule_df, new_class_details):
    """
    Checks if manually assigning new_class_details would conflict with the existing schedule_df.
    
    Args:
        schedule_df (pd.DataFrame): The current generated schedule.
        new_class_details (dict): Dict with 'Instructor', 'Room', 'Day', 'Time Slot'.
                                 Can also include 'Subject Code', 'Section' for error messages.
    
    Returns:
        list: A list of conflict messages. Empty if no conflicts.
    """
    found_conflicts = []
    
    if schedule_df is None or schedule_df.empty:
        return [] # No existing schedule, so no conflicts with it

    teacher = new_class_details['Instructor']
    room = new_class_details['Room']
    day = new_class_details['Day']
    time_slot = new_class_details['Time Slot']

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
                st.warning(f"Subject Code '{subject_code}' (curriculum) not in subjects list for section {section_name}.")
    return classes_list

def generate_schedule_attempt(classes_to_schedule, parsed_instructors_orig, parsed_rooms_orig):
    if not classes_to_schedule or not parsed_instructors_orig or not parsed_rooms_orig:
        st.warning("Missing necessary data for scheduling (classes, instructors, or rooms).")
        return [], []

    import copy
    current_instructors_data = copy.deepcopy(parsed_instructors_orig)
    current_rooms_availability = copy.deepcopy(parsed_rooms_orig)
    
    generated_schedule = []
    conflicts = []
    instructor_busy_slots = set() # Stores (instructor_name, day, time_slot)
    section_busy_slots = set() # NEW: Stores (section_name, day, time_slot)
    
    # --- !!! NEW: Sorting classes_to_schedule !!! ---
    # Sort by number of students in descending order (largest classes first)
    # This assumes each item in classes_to_schedule is a dictionary
    # and has a key like 'section_students' (adjust key name if different)
    try:
        # Add a check to ensure 'section_students' exists and is numeric, or handle potential errors
        valid_classes_for_sorting = []
        for c in classes_to_schedule:
            if isinstance(c.get('section_students'), (int, float)):
                valid_classes_for_sorting.append(c)
            else:
                # Handle classes with missing or non-numeric student counts if necessary
                # For now, we might just exclude them from sorting or log a warning
                print(f"Warning: Class {c.get('subject_code')} for {c.get('section_name')} has invalid student count for sorting: {c.get('section_students')}")
                # Option: Add them to the end without sorting, or raise an error
                # For simplicity, let's assume they get appended if not sortable by student count
                # but it's better if all classes have this field correctly populated.
                # For now, this example just proceeds with sortable items.

        # If all classes are valid for sorting by student count:
        sorted_classes_to_schedule = sorted(
            valid_classes_for_sorting,  # Use the filtered list
            key=lambda x: x['section_students'], 
            reverse=True
        )
        # Add back any classes that couldn't be sorted by student count (if any were filtered out)
        # This part can be adjusted based on how you want to handle invalid student counts.
        # For now, we'll just use the sorted list of valid classes.
        
        print(f"Scheduling order: First class to attempt (largest): {sorted_classes_to_schedule[0]['subject_code']} for {sorted_classes_to_schedule[0]['section_name']} ({sorted_classes_to_schedule[0]['section_students']} students)")
        print(f"Scheduling order: Last class to attempt (smallest): {sorted_classes_to_schedule[-1]['subject_code']} for {sorted_classes_to_schedule[-1]['section_name']} ({sorted_classes_to_schedule[-1]['section_students']} students)")

    except KeyError as e:
        # This means 'section_students' key was missing in one of the class_info dicts
        # st.error(f"Error sorting classes: Missing key {e}. Scheduling in original order.") # If using tabs
        print(f"Error sorting classes: Missing key {e}. Scheduling in original order.")
        sorted_classes_to_schedule = classes_to_schedule # Fallback to original order
    except Exception as e:
        print(f"An unexpected error occurred during sorting: {e}. Scheduling in original order.")
        sorted_classes_to_schedule = classes_to_schedule # Fallback

    # --- End of Sorting ---

    # Now, loop through the sorted_classes_to_schedule
    for class_info in sorted_classes_to_schedule: # USE THE SORTED LIST HERE
        section_name = class_info['section_name']
        subject_code = class_info['subject_code']
        # ... (rest of your variable assignments from class_info)
        subject_name = class_info['subject_name']
        required_spec = class_info['required_specialization']
        num_students = class_info['section_students'] # This is the key used for sorting

        slot_assigned_for_this_class = False
        
        # --- Pre-checks for more detailed "Unscheduled" reasons ---
        # (These checks look at the *original* availability before any assignments in this run)
        
        # 1. Find all teachers specialized for this subject
        specialized_teachers = [
            instr_name for instr_name, details in parsed_instructors_orig.items()
            if required_spec in details['specializations']
        ]
        if not specialized_teachers:
            conflicts.append({
                'type': 'Unscheduled Class', 'section': section_name, 'subject': subject_code,
                'students': num_students, 'required_specialization': required_spec,
                'reason': f"No teachers found with specialization: {required_spec}."
            })
            continue 

        # 2. Check if any of these specialized teachers have ANY availability
        # (This is a basic check; doesn't mean they are free *now* after other assignments)
        at_least_one_specialized_teacher_has_some_availability = any(
            parsed_instructors_orig[name]['availability'] for name in specialized_teachers
        )
        if not at_least_one_specialized_teacher_has_some_availability:
            conflicts.append({
                'type': 'Unscheduled Class', 'section': section_name, 'subject': subject_code,
                'students': num_students, 'required_specialization': required_spec,
                'reason': f"Teachers with spec '{required_spec}' exist, but none have any listed availability slots."
            })
            continue

        # 3. Find all rooms that meet capacity (ignoring their current availability for this pre-check)
        suitable_rooms_by_capacity = []
        for room_name_iter, room_slots_iter in parsed_rooms_orig.items(): 
            if any(details['capacity'] >= num_students for details in room_slots_iter.values()):
                 suitable_rooms_by_capacity.append(room_name_iter)
        
        if not suitable_rooms_by_capacity:
            conflicts.append({
                'type': 'Unscheduled Class', 'section': section_name, 'subject': subject_code,
                'students': num_students, 'required_specialization': required_spec,
                'reason': f"No rooms found with capacity >= {num_students} students."
            })
            continue
        # --- End of Pre-checks ---


        # --- Main Assignment Loop (using current_instructors_data and current_rooms_availability) ---
        instructor_names_to_try = list(current_instructors_data.keys()) # Or sorted list

        for instructor_name in instructor_names_to_try:
            if slot_assigned_for_this_class: break
            instr_details = current_instructors_data[instructor_name]
            if required_spec not in instr_details['specializations']: continue

            for day, time_slot in list(instr_details['availability']): # Iterate over original availability slots
                if slot_assigned_for_this_class: break
                if (instructor_name, day, time_slot) in instructor_busy_slots: continue
                                # --- NEW CHECK: Section Schedule Clash (Proactive check) ---
                # Check if the current section is already scheduled for ANY subject at this day/time
                if (section_name, day, time_slot) in section_busy_slots:
                    continue # This section is already busy, this (day, time_slot) is not viable for this section. Try next slot.

                for room_name, room_time_slots_data in current_rooms_availability.items():
                    if slot_assigned_for_this_class: break
                    if (day, time_slot) in room_time_slots_data and \
                       room_time_slots_data[(day, time_slot)]['is_available']:
                        room_slot_details = room_time_slots_data[(day, time_slot)]
                        if room_slot_details['capacity'] >= num_students:
                            
                            # Assign and mark busy
                            room_time_slots_data[(day, time_slot)]['is_available'] = False
                            instructor_busy_slots.add((instructor_name, day, time_slot))
                            generated_schedule.append({
                                'Section': section_name, 'Subject Code': subject_code, 'Subject Name': subject_name,
                                'Instructor': instructor_name, 'Room': room_name, 'Day': day, 'Time Slot': time_slot,
                                'Students': num_students, 'Room Capacity': room_slot_details['capacity']
                            })
                            slot_assigned_for_this_class = True; break 
            if slot_assigned_for_this_class: break 

        if not slot_assigned_for_this_class:
            # If pre-checks passed, the most likely reason now is no common slot or all suitable slots already taken
            conflicts.append({
                'type': 'Unscheduled Class', 'section': section_name, 'subject': subject_code,
                'students': num_students, 'required_specialization': required_spec,
                'reason': 'Specialized teachers & suitable rooms exist, but no common available time slot found, or all suitable slots taken by prior assignments.'
            })
            
    # --- Post-scheduling Conflict Checks (Teacher and Room Double Bookings) ---
    # (Keep this section as it was, it's still a good final check)
    teacher_schedule_map = {} 
    for entry in generated_schedule:
        key = (entry['Instructor'], entry['Day'], entry['Time Slot'])
        teacher_schedule_map.setdefault(key, []).append(f"{entry['Subject Code']} for {entry['Section']}")
    for key, classes_involved_list in teacher_schedule_map.items():
        if len(classes_involved_list) > 1:
            conflicts.append({'type': 'Teacher Double Booked (Post-Check)', 'instructor': key[0], 'day': key[1], 
                              'time_slot': key[2], 'classes_involved': ', '.join(classes_involved_list),
                              'reason': f"Instructor {key[0]} scheduled for multiple classes."})
    room_schedule_map = {}
    for entry in generated_schedule:
        key = (entry['Room'], entry['Day'], entry['Time Slot'])
        room_schedule_map.setdefault(key, []).append(f"{entry['Subject Code']} for {entry['Section']}")
    for key, classes_involved_list in room_schedule_map.items():
        if len(classes_involved_list) > 1:
            conflicts.append({'type': 'Room Double Booked (Post-Check)', 'room': key[0], 'day': key[1], 
                              'time_slot': key[2], 'classes_involved': ', '.join(classes_involved_list),
                              'reason': f"Room {key[0]} scheduled for multiple classes."})
            
    return generated_schedule, conflicts

def load_all_data_from_session_uploads():
    # Sections
    sections_file_obj = st.session_state.get('sections_upload_main')
    if sections_file_obj is not None and st.session_state.sections_df is None:
        try:
            df = pd.read_csv(sections_file_obj); st.session_state.sections_df = df
            st.session_state.data_loaded_flags['sections'] = True; st.success("Sections data loaded!")
        except Exception as e: st.error(f"Error Sections: {e}"); st.session_state.data_loaded_flags['sections'] = False
    # Instructors
    instructors_file_obj = st.session_state.get('instructors_upload_main')
    if instructors_file_obj is not None and st.session_state.instructors_raw_df is None:
        try:
            df = pd.read_csv(instructors_file_obj); st.session_state.instructors_raw_df = df
            st.session_state.data_loaded_flags['instructors_raw'] = True; st.success("Instructor raw data loaded!")
        except Exception as e: st.error(f"Error Instructors: {e}"); st.session_state.data_loaded_flags['instructors_raw'] = False
    # Subjects
    subjects_file_obj = st.session_state.get('subjects_upload_main')
    if subjects_file_obj is not None and st.session_state.subjects_df is None:
        try:
            df = pd.read_csv(subjects_file_obj); st.session_state.subjects_df = df
            st.session_state.data_loaded_flags['subjects'] = True; st.success("Subjects data loaded!")
        except Exception as e: st.error(f"Error Subjects: {e}"); st.session_state.data_loaded_flags['subjects'] = False
    # Rooms
    rooms_file_obj = st.session_state.get('rooms_upload_main')
    if rooms_file_obj is not None and st.session_state.rooms_raw_df is None:
        try:
            df = pd.read_csv(rooms_file_obj); st.session_state.rooms_raw_df = df
            st.session_state.data_loaded_flags['rooms_raw'] = True; st.success("Rooms raw data loaded!")
        except Exception as e: st.error(f"Error Rooms: {e}"); st.session_state.data_loaded_flags['rooms_raw'] = False
    # Curriculum
    curriculum_file_obj = st.session_state.get('curriculum_upload_main')
    if curriculum_file_obj is not None and st.session_state.curriculum_df is None:
        try:
            df = pd.read_csv(curriculum_file_obj); st.session_state.curriculum_df = df
            st.session_state.data_loaded_flags['curriculum'] = True; st.success("Curriculum mapping loaded!")
        except Exception as e: st.error(f"Error Curriculum: {e}"); st.session_state.data_loaded_flags['curriculum'] = False

def create_timetable_grid(schedule_df, entity_type=None, selected_entity=None):
    # Ensure TIME_SLOTS_ORDER_24HR and TIME_SLOTS_DISPLAY are accessible here
    # (either global or passed as arguments)

    if schedule_df is None or schedule_df.empty:
        # Use TIME_SLOTS_DISPLAY for the index of the empty grid
        return pd.DataFrame(index=TIME_SLOTS_DISPLAY, columns=DAYS_ORDER).fillna('')

    schedule_df['Day'] = schedule_df['Day'].str.upper()

    filtered_schedule = schedule_df.copy()
    if entity_type and selected_entity and selected_entity != "All":
        # ... (your existing filtering logic) ...
        if entity_type == "Room" and "Room" in filtered_schedule.columns:
            filtered_schedule = filtered_schedule[filtered_schedule['Room'] == selected_entity]
        elif entity_type == "Section" and "Section" in filtered_schedule.columns:
            filtered_schedule = filtered_schedule[filtered_schedule['Section'] == selected_entity]
        elif entity_type == "Instructor" and "Instructor" in filtered_schedule.columns:
            filtered_schedule = filtered_schedule[filtered_schedule['Instructor'] == selected_entity]
    
    if filtered_schedule.empty and selected_entity != "All":
        return pd.DataFrame(index=TIME_SLOTS_DISPLAY, columns=DAYS_ORDER).fillna('')

    # Initialize timetable with AM/PM display time slots as index
    timetable = pd.DataFrame(index=TIME_SLOTS_DISPLAY, columns=DAYS_ORDER)
    timetable = timetable.fillna('') 

    for _, row in filtered_schedule.iterrows():
        day = row['Day']
        time_slot_24hr_data = row['Time Slot'] # This is the 24hr string from your data
        
        # Convert the 24hr data time slot to its corresponding display format for index lookup
        display_time_slot_for_index = format_time_slot_for_display(time_slot_24hr_data)
        
        cell_content = f"{row.get('Subject Code', 'N/A')}"
        # ... (your existing cell_content formatting logic based on entity_type) ...
        if entity_type == "Room": 
            cell_content += f"\nSec: {row.get('Section', 'N/A')}\nProf: {row.get('Instructor', 'N/A')[:15]}" 
        elif entity_type == "Section": 
             cell_content += f"\nRoom: {row.get('Room', 'N/A')}\nProf: {row.get('Instructor', 'N/A')[:30]}"
        elif entity_type == "Instructor": 
             cell_content += f"\nRoom: {row.get('Room', 'N/A')}\nSec: {row.get('Section', 'N/A')}"
        else: 
            cell_content += f"\n{row.get('Section', 'N/A')}\n{row.get('Instructor', 'N/A')[:15]}\n{row.get('Room', 'N/A')}"


        # Use the display_time_slot_for_index to locate the row in the timetable
        if day in timetable.columns and display_time_slot_for_index in timetable.index:
            if timetable.loc[display_time_slot_for_index, day] == '':
                timetable.loc[display_time_slot_for_index, day] = cell_content
            else:
                timetable.loc[display_time_slot_for_index, day] += f"\n---\n{cell_content}"
        else:
            print(f"Warning: Day '{day}' or Display Time Slot '{display_time_slot_for_index}' (from {time_slot_24hr_data}) not in defined grid for: {cell_content}")

    return timetable


# --- Streamlit App Layout Starts Here ---
st.set_page_config(layout="wide") 
st.title("Honorians InSync - Automated Resource and Scheduling Management System")


# --- Session State Initialization ---
# (Ensure this is complete as per previous discussions)
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
# --- End of Session State Initialization ---


# --- Define Tabs (Adding a new first tab) ---
tab_about, tab_upload, tab_run, tab_schedule, tab_conflicts = st.tabs([
    "Workflow & About",             # New first tab
    "1. Upload & Verify Data", 
    "2. Run Scheduler", 
    "3. View Generated Schedule", 
    "4. Resolve Conflicts"
])

# --- Tab 0: Workflow & About ---
with tab_about:
    # ---------- HERO ----------
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(
            "https://dhvsu.edu.ph/images/DHVSU-LOGO.png",  # replace!
            caption="Don Honorio Ventura State University",
            use_container_width=True,
        )
    with col2:
        st.title("Automated Scheduling System")
        st.write(
            "Honorians InSync is a web-based Automated Scheduling & Resource Management System (ASRMS) designed to simplify and streamline course scheduling and room resource management at the College of Business Administration, Don Honorio Ventura State University (DHVSU)."
        )
    st.divider()

    # ---------- HOW IT WORKS ----------
    st.subheader("System Workflow")
    step_cols = st.columns(4)
    steps = [
        ("1️⃣ Upload & Verify", "Upload CSVs for sections, instructors, subjects, rooms, and curriculum."),
        ("2️⃣ Run Scheduler", "Click **Generate** to let the greedy algorithm build a draft timetable."),
        ("3️⃣ View Schedule", "Filter by room, section, or instructor to inspect the result."),
        ("4️⃣ Resolve Conflicts", "Interactively fix unscheduled classes and double bookings."),
    ]
    for col, (title, blurb) in zip(step_cols, steps):
        with col:
            st.markdown(f"#### {title}")
            st.write(blurb)

    st.divider()

    # ---------- KEY FEATURES ----------
    st.subheader("🔑 Key Components")
    st.markdown(
        """
    * **Automated generation** — teacher availability, subject specialization, and room capacity all considered  
    * **Conflict detection and resolution** — double bookings, overloads, unscheduled classes  
    * **Interactive dashboard** — timetable view with powerful filters 
    """
    )

    # ---------- DATA BLUEPRINT ----------
    st.subheader("📂 Data Blueprint (CSV headers)")
    col_sec, col_ins, col_sub, col_room, col_cur = st.columns(5) # Still use columns for layout

    with col_sec:
        st.markdown("""
        <div class="data-blueprint-item">
            <p class="item-label"><span class="emoji-icon">📝</span> Sections Data</p>
            <p class="item-headers">Course, Year Level, Section, Students</p>
        </div>
        """, unsafe_allow_html=True)

    with col_ins:
        st.markdown("""
        <div class="data-blueprint-item">
            <p class="item-label"><span class="emoji-icon">🧑‍🏫</span> Instructor Data</p>
            <p class="item-headers"> Instructor, Day, Time Slot, Department, Specialization</p>
        </div>
        """, unsafe_allow_html=True)

    with col_sub:
        st.markdown("""
        <div class="data-blueprint-item">
            <p class="item-label"><span class="emoji-icon">📚</span> Subjects Data</p>
            <p class="item-headers">Subject Code, Subject Name, Required Specialization</p>
        </div>
        """, unsafe_allow_html=True)

    with col_room:
        st.markdown("""
        <div class="data-blueprint-item">
            <p class="item-label"><span class="emoji-icon">🏫</span> Rooms Data</p>
            <p class="item-headers">Room, Day, Time Slot, Max Capacity</p>
        </div>
        """, unsafe_allow_html=True)

    with col_cur:
        st.markdown("""
        <div class="data-blueprint-item">
            <p class="item-label"><span class="emoji-icon">🗺️</span> Curriculum Mapping</p>
            <p class="item-headers">Course, Year Level, Subject Code</p>
        </div>
        """, unsafe_allow_html=True)

# --- Tab 1: Upload & Verify Data ---
with tab_upload:
    st.header("Upload Data Files")
    # File Uploaders
    st.file_uploader("Sections Data", type="csv", key="sections_upload_main")
    st.file_uploader("Instructor Data", type="csv", key="instructors_upload_main")
    st.file_uploader("Subjects Data", type="csv", key="subjects_upload_main")
    st.file_uploader("Rooms Data", type="csv", key="rooms_upload_main")
    st.file_uploader("Curriculum Mapping Data", type="csv", key="curriculum_upload_main")

    # Attempt to load data if files are uploaded
    load_all_data_from_session_uploads()

    # Process data if raw data is loaded and not yet processed
    if st.session_state.data_loaded_flags.get('instructors_raw', False) and \
       st.session_state.instructors_raw_df is not None and \
       st.session_state.parsed_instructors is None:
        st.session_state.parsed_instructors = process_instructor_data(st.session_state.instructors_raw_df)
        if st.session_state.parsed_instructors is not None: st.info("Instructor data processed.")

    if st.session_state.data_loaded_flags.get('rooms_raw', False) and \
       st.session_state.rooms_raw_df is not None and \
       st.session_state.parsed_rooms is None:
        st.session_state.parsed_rooms = process_room_data(st.session_state.rooms_raw_df)
        if st.session_state.parsed_rooms is not None: st.info("Room data processed.")
    
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
            st.info(f"{len(st.session_state.classes_to_be_scheduled)} class instances identified.")
        elif st.session_state.sections_df is not None: # Check if other DFs were there
             st.warning("No class instances generated from curriculum.")


    st.markdown("---")
    st.header("Data Verification")
    # Sections
    if st.session_state.sections_df is not None:
        with st.expander("Sections Data Preview"): st.dataframe(st.session_state.sections_df.head())
    # Instructors (Raw and Processed)
    if st.session_state.instructors_raw_df is not None:
        with st.expander("Instructors Raw Data Preview"): st.dataframe(st.session_state.instructors_raw_df.head())
        if st.session_state.parsed_instructors:
            with st.expander("Processed Instructor Data (Sample)"):
                num_to_sample = min(2, len(st.session_state.parsed_instructors))
                sample = {k: st.session_state.parsed_instructors[k] for k in list(st.session_state.parsed_instructors.keys())[:num_to_sample]}
                if sample: st.json(sample)
                st.caption(f"Total unique instructors: {len(st.session_state.parsed_instructors)}")
    # Subjects
    if st.session_state.subjects_df is not None:
        with st.expander("Subjects Data Preview"): st.dataframe(st.session_state.subjects_df.head())
    # Rooms (Raw and Processed)
    if st.session_state.rooms_raw_df is not None:
        with st.expander("Rooms Raw Data Preview"): st.dataframe(st.session_state.rooms_raw_df.head())
        if st.session_state.parsed_rooms:
            with st.expander("Processed Room Data (Sample - JSON friendly)"): # Your JSON fix here
                num_to_sample = min(1, len(st.session_state.parsed_rooms))
                json_friendly_sample = {}
                for room_key in list(st.session_state.parsed_rooms.keys())[:num_to_sample]:
                    room_dt = st.session_state.parsed_rooms[room_key]
                    json_friendly_sample[room_key] = {f"{d} {ts}": dtls for (d, ts), dtls in room_dt.items()}
                if json_friendly_sample: st.json(json_friendly_sample)
                st.caption(f"Total unique rooms: {len(st.session_state.parsed_rooms)}")
    # Curriculum
    if st.session_state.curriculum_df is not None:
        with st.expander("Curriculum Mapping Preview"): st.dataframe(st.session_state.curriculum_df.head())
    # Classes to be scheduled
    if st.session_state.classes_to_be_scheduled:
        with st.expander(f"Identified Classes for Scheduling Preview (Top {min(5, len(st.session_state.classes_to_be_scheduled))})"):
            st.dataframe(pd.DataFrame(st.session_state.classes_to_be_scheduled[:5]))

# --- Tab 2: Run Scheduler ---
with tab_run:
    st.header("Run the Automated Scheduler")
    
    ready_to_schedule_check = (
        st.session_state.classes_to_be_scheduled and 
        st.session_state.parsed_instructors and 
        st.session_state.parsed_rooms
    )

    if not ready_to_schedule_check:
        st.warning("Please ensure all data is uploaded and processed in Tab 1 before running the scheduler.")
    
    if st.button("Generate Class Schedule", disabled=not ready_to_schedule_check, type="primary"):
        with st.spinner("Generating schedule... This may take a moment."):
            schedule_result, conflicts_result = generate_schedule_attempt(
                st.session_state.classes_to_be_scheduled,
                st.session_state.parsed_instructors,
                st.session_state.parsed_rooms
            )
        st.session_state.generated_schedule_df = pd.DataFrame(schedule_result)
        st.session_state.conflicts = conflicts_result
        
        if st.session_state.generated_schedule_df is not None and not st.session_state.generated_schedule_df.empty:
            st.success(f"Schedule generation complete! {len(st.session_state.generated_schedule_df)} classes scheduled.")
            if st.session_state.conflicts:
                 st.warning(f"{len(st.session_state.conflicts)} conflicts or issues found. Check Tab 4.")
            else:
                 st.info("No conflicts detected from the scheduler run.")
        elif st.session_state.conflicts:
             st.error(f"Scheduler run complete. No classes scheduled. {len(st.session_state.conflicts)} conflicts/issues found.")
        else:
             st.info("Scheduler run complete. No classes scheduled and no conflicts reported (check input data and curriculum).")

# --- Tab 3: View Generated Schedule ---
with tab_schedule:
    st.header("Generated Class Schedule")

    if st.session_state.generated_schedule_df is not None and not st.session_state.generated_schedule_df.empty:
        
        # --- Add Filters ---
        st.sidebar.subheader("Timetable Filters (Tab 3)") # Add filters to sidebar for this tab
        
        filter_type_options = ["Overall View", "Room", "Section", "Instructor"]
        selected_filter_type = st.sidebar.selectbox(
            "Filter timetable by:", 
            filter_type_options, 
            key="timetable_filter_type"
        )

        entity_list = ["All"] # Default for "Overall View"
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
        # --- End Filters ---

        # Ensure Day column is uppercase before creating timetable
        schedule_to_display = st.session_state.generated_schedule_df.copy()
        
        if 'Day' in schedule_to_display.columns:
             schedule_to_display['Day'] = schedule_to_display['Day'].astype(str).str.upper() # Ensure it's string then upper

        if selected_filter_type == "Overall View":
            st.subheader("Overall Master Schedule (First Available per Slot)")
            # For overall view, the create_timetable_grid might get crowded if multiple classes are in one slot
            # The current function will append them. You might want a different strategy for "Overall".
            # For now, let's just pass None as entity_type to get the default cell content.
            timetable_grid_df = create_timetable_grid(schedule_to_display, None, None)

        elif selected_entity and selected_entity != "All":
            st.subheader(f"Schedule for {selected_filter_type}: {selected_entity}")
            timetable_grid_df = create_timetable_grid(schedule_to_display, selected_filter_type, selected_entity)
        
        elif selected_entity == "All" and selected_filter_type != "Overall View": # E.g. "Room" selected, but then "All Rooms"
            st.info(f"Displaying combined schedule for all {selected_filter_type}s. This might be crowded.")
            # This could show all classes by iterating and overlaying, or just the first found.
            # For simplicity, let's show the same as Overall for now, or you can choose not to display.
            timetable_grid_df = create_timetable_grid(schedule_to_display, None, None) # Or an empty grid

        else: # Should not happen if logic is correct
            timetable_grid_df = pd.DataFrame(index=TIME_SLOTS_ORDER_24HR, columns=DAYS_ORDER).fillna('')


        if not timetable_grid_df.empty:
            # --- HTML Rendering ---
            st.markdown("#### Timetable Grid")

            # Prepare DataFrame for HTML: replace newlines with <br> for multi-line cell content
            html_ready_df = timetable_grid_df.astype(str).replace({r'\n': '<br>'}, regex=True)
            
            # Convert DataFrame to HTML table string
            # escape=False allows <br> to render as line breaks
            # na_rep="" makes NaN values appear as empty cells
            # classes="schedule_table" adds a CSS class for styling
            # index_names=False can hide the index name "Time Slot" if you don't want it
            # index=True ensures the time slot index is included
            html_table = html_ready_df.to_html(escape=False, na_rep="", classes="schedule_table streamlit_df", index=True, index_names=False, border=0)

            # Custom CSS for the table to make it look more like a grid
            # and ensure content wraps and respects <br>
            table_css = """
            <style>
                table.schedule_table {
                    border-collapse: collapse; /* Crucial for grid lines */
                    width: 100%;
                    font-size: 0.85em; /* Adjust as needed */
                    table-layout: fixed; /* Helps with column widths if needed */
                }
                table.schedule_table th, table.schedule_table td {
                    border: 1px solid #cccccc; /* Grid lines */
                    padding: 6px;
                    text-align: center; /* Center align text */
                    vertical-align: top; /* Align content to the top of the cell */
                    height: 60px; /* Minimum height for cells, adjust as needed */
                    word-wrap: break-word; /* Wrap long text */
                    white-space: pre-wrap; /* Respects <br> and also wraps text */
                }
                table.schedule_table th { /* Styling for header row (Days) */
                    background-color: #f2f2f2; /* Light grey background for headers */
                    font-weight: bold;
                }
                table.schedule_table td:first-child { /* Styling for first column (Time Slots) */
                    font-weight: bold;
                    text-align: center; /* Center time slots */
                    background-color: #f2f2f2;
                     /* For sticky first column (Time) - might need more robust CSS for full effect across browsers */
                    /* position: -webkit-sticky; 
                    position: sticky;
                    left: 0;
                    z-index: 1; */
                }
            </style>
            """
            
            st.markdown(table_css, unsafe_allow_html=True)
            st.markdown(html_table, unsafe_allow_html=True)

        else:
             st.info(f"No schedule data to display for the selected filter.")
            
    elif st.session_state.get('generated_schedule_df') is not None and \
         st.session_state.generated_schedule_df.empty:
        st.info("No classes were scheduled. Please run the scheduler or check data.")
    else:
        st.info("Scheduler has not been run yet.")

# --- Tab 4: View Conflicts & Issues ---
with tab_conflicts:
    st.header("Resolve Scheduling Conflicts")

    if 'selected_conflict_to_resolve_idx' not in st.session_state:
        st.session_state.selected_conflict_to_resolve_idx = None 
    if 'selected_conflict_type' not in st.session_state: # To know what kind of conflict we are resolving
        st.session_state.selected_conflict_type = None
    if 'manual_assignment_feedback' not in st.session_state:
        st.session_state.manual_assignment_feedback = None
    if 'class_to_modify_from_double_booking_idx' not in st.session_state: # For teacher double booking
         st.session_state.class_to_modify_from_double_booking_idx = None


    if st.session_state.conflicts:
        st.subheader("Overall Conflict Summary")
        conflicts_df_display = pd.DataFrame(list(st.session_state.conflicts))
        st.dataframe(conflicts_df_display, height=200)
        st.markdown("---")

        # --- Section for Selecting ANY Conflict Type to Resolve ---
        st.subheader("Select a Conflict to Resolve:")

        conflict_options = ["Select a conflict..."]
        # Store more info than just display string for easier lookup
        resolvable_conflict_details = [] 

        for idx, c in enumerate(st.session_state.conflicts):
            display_str = f"Orig.Idx {idx}: {c['type']} - "
            if c['type'] == 'Unscheduled Class':
                display_str += f"Sec: {c.get('section', 'N/A')}, Subj: {c.get('subject', 'N/A')}"
                # Only add if it's the type of unscheduled we can handle now
                if "no common available time slot found" in c.get('reason', '').lower() or \
                   "suitable combination found" in c.get('reason', '').lower():
                    conflict_options.append(display_str)
                    resolvable_conflict_details.append({'display': display_str, 'original_index': idx, 'type': c['type']})
            elif c['type'] == 'Teacher Double Booked (Post-Check)':
                display_str += f"Teacher: {c.get('instructor', 'N/A')} at {c.get('day','N/A')} {c.get('time_slot','N/A')}"
                conflict_options.append(display_str)
                resolvable_conflict_details.append({'display': display_str, 'original_index': idx, 'type': c['type']})
            # Add elif for 'Room Double Booked (Post-Check)' later

        selected_conflict_display_str_main = st.selectbox(
            "Choose a conflict:",
            conflict_options,
            key="main_conflict_selector_tab4"
        )

        # Update session state for selected conflict index and type
        if selected_conflict_display_str_main != "Select a conflict...":
            for item in resolvable_conflict_details:
                if item['display'] == selected_conflict_display_str_main:
                    st.session_state.selected_conflict_to_resolve_idx = item['original_index']
                    st.session_state.selected_conflict_type = item['type']
                    # Reset sub-selection for teacher double booking if a new conflict is chosen
                    if st.session_state.selected_conflict_type != 'Teacher Double Booked (Post-Check)':
                        st.session_state.class_to_modify_from_double_booking_idx = None
                    break
        else:
            st.session_state.selected_conflict_to_resolve_idx = None
            st.session_state.selected_conflict_type = None
            st.session_state.manual_assignment_feedback = None
            st.session_state.class_to_modify_from_double_booking_idx = None


        # --- Display Resolution Form based on Selected Conflict Type ---
        if st.session_state.selected_conflict_to_resolve_idx is not None:
            conflict_original_idx = st.session_state.selected_conflict_to_resolve_idx
            
            if not (0 <= conflict_original_idx < len(st.session_state.conflicts)):
                st.warning("Selected conflict is no longer valid. Please re-select.")
                st.session_state.selected_conflict_to_resolve_idx = None
                st.session_state.selected_conflict_type = None
            else:
                conflict_to_resolve = st.session_state.conflicts[conflict_original_idx]

                # --- A. Resolver for "Unscheduled Class" ---
                if st.session_state.selected_conflict_type == 'Unscheduled Class':
                    # ... (displaying conflict details and form setup with selectboxes) ...
                    # This is the form for unscheduled classes
                    with st.form(key=f"unscheduled_form_{conflict_original_idx}"):
                        # (Your selectboxes for selected_teacher, selected_room, selected_day, selected_time_slot)
                        # ...
                        sel_teacher_options = ["Select..."] 
                        if st.session_state.get('parsed_instructors'): # Use .get for safety
                            sel_teacher_options.extend(sorted([name for name, details in st.session_state['parsed_instructors'].items() if conflict_to_resolve['required_specialization'] in details['specializations']]))
                        selected_teacher = st.selectbox("Select Teacher:", sel_teacher_options, key=f"uns_teacher_{conflict_original_idx}")
                        
                        sel_room_options = ["Select..."]
                        if st.session_state.get('parsed_rooms'):
                            sel_room_options.extend(sorted([name for name, room_slots in st.session_state['parsed_rooms'].items() if any(details['capacity'] >= conflict_to_resolve['students'] for details in room_slots.values())]))
                        selected_room = st.selectbox("Select Room:", sel_room_options, key=f"uns_room_{conflict_original_idx}")

                        selected_day = st.selectbox("Select Day:", ["Select..."] + DAYS_ORDER, key=f"uns_day_{conflict_original_idx}")
                        selected_time_slot = st.selectbox("Select Time Slot:", ["Select..."] + TIME_SLOTS_ORDER_24HR, key=f"uns_time_{conflict_original_idx}")

                        submitted_unscheduled_fix = st.form_submit_button("Force Assign Unscheduled Class") # Changed button label

                        if submitted_unscheduled_fix:
                            st.session_state.manual_assignment_feedback = None 
                            if selected_teacher == "Select..." or selected_room == "Select..." or \
                                selected_day == "Select..." or selected_time_slot == "Select...":
                                st.error("Please make full selections for Teacher, Room, Day, and Time Slot to force assign.")
                            else:
                                # --- "FORCE ASSIGN" LOGIC for Unscheduled Class ---
                                # We are NOT calling check_manual_assignment_conflicts here.
                                # We are NOT doing pre-assignment verifications for capacity/specialization here.
                                # The admin is overriding all constraints for this specific action.

                                # Get Subject Name (safer lookup)
                                subject_name_val = 'N/A_SubjName'
                                if st.session_state.get('subjects_df') is not None:
                                    subj_series = st.session_state['subjects_df'][st.session_state['subjects_df']['Subject Code'] == conflict_to_resolve['subject']]['Subject Name']
                                    if not subj_series.empty:
                                        subject_name_val = subj_series.iloc[0]
                                
                                # Get Room Capacity (safer lookup) - for information, not for constraint checking
                                room_capacity_val = 'N/A_Cap'
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
                                    'Room Capacity': room_capacity_val, # Informational
                                    'Assignment Type': 'Manual (Forced)' 
                                }

                                # Add directly to the schedule
                                if st.session_state.get('generated_schedule_df') is None:
                                    st.session_state.generated_schedule_df = pd.DataFrame([forced_class_details])
                                else:
                                    new_row_df = pd.DataFrame([forced_class_details])
                                    st.session_state.generated_schedule_df = pd.concat(
                                        [st.session_state.generated_schedule_df, new_row_df], 
                                        ignore_index=True
                                    )
                                
                                # Remove the resolved "Unscheduled Class" conflict from the list
                                st.session_state.conflicts.pop(conflict_original_idx) 
                                                                    
                                feedback_msg = (f"FORCE ASSIGNED: {forced_class_details['Subject Code']} "
                                                f"for {forced_class_details['Section']} to {forced_class_details['Instructor']} "
                                                f"in {forced_class_details['Room']} at {forced_class_details['Day']} {forced_class_details['Time Slot']}.\n"
                                                f"Warning: This assignment was forced and may have created new conflicts (e.g., double bookings). "
                                                f"Please re-run conflict checks or review the schedule carefully.")
                                st.warning(feedback_msg) # Use st.warning for forced assignments
                                st.session_state.manual_assignment_feedback = feedback_msg
                                
                                # Clear selection and rerun
                                st.session_state.selected_conflict_to_resolve_idx = None 
                                st.session_state.selected_conflict_type = None
                                st.rerun() 

                # --- B. Resolver for "Teacher Double Booked" ---
                elif st.session_state.selected_conflict_type == 'Teacher Double Booked (Post-Check)':
                    st.markdown(f"**Resolving Teacher Double Booking (Conflict Orig.Idx: {conflict_original_idx}):**\n"
                                f"- Teacher: **{conflict_to_resolve['instructor']}**\n"
                                f"- Day: **{conflict_to_resolve['day']}**, Time: **{conflict_to_resolve['time_slot']}**\n"
                                f"- Classes Involved: **{conflict_to_resolve['classes_involved']}**")
                    
                    # Find the actual class entries in generated_schedule_df that are conflicting
                    conflicting_schedule_entries = []
                    if st.session_state.generated_schedule_df is not None:
                        conflicting_schedule_entries = st.session_state.generated_schedule_df[
                            (st.session_state.generated_schedule_df['Instructor'] == conflict_to_resolve['instructor']) &
                            (st.session_state.generated_schedule_df['Day'].str.upper() == conflict_to_resolve['day'].upper()) & # Ensure case consistency
                            (st.session_state.generated_schedule_df['Time Slot'] == conflict_to_resolve['time_slot'])
                        ].copy() # Use .copy()
                        # Add an original DataFrame index to each entry for easy reference
                        conflicting_schedule_entries['original_df_index'] = conflicting_schedule_entries.index 
                    
                    if not conflicting_schedule_entries.empty:
                        st.markdown("Select one class to modify/reschedule:")
                        class_options_to_modify = ["Select a class..."] + \
                            [f"Idx {row['original_df_index']}: {row['Subject Code']} for Sec {row['Section']} in Room {row['Room']}" 
                             for _, row in conflicting_schedule_entries.iterrows()]
                        
                        selected_class_str_to_modify = st.selectbox(
                            "Class to Reschedule:", 
                            class_options_to_modify, 
                            key=f"tdb_class_select_{conflict_original_idx}"
                        )

                        # Store the original_df_index of the class chosen to be modified
                        if selected_class_str_to_modify != "Select a class...":
                            # Extract original_df_index from the display string
                            try:
                                df_idx_to_modify = int(selected_class_str_to_modify.split(':')[0].replace('Idx','').strip())
                                st.session_state.class_to_modify_from_double_booking_idx = df_idx_to_modify
                            except ValueError:
                                 st.session_state.class_to_modify_from_double_booking_idx = None # Invalid format
                        else:
                            st.session_state.class_to_modify_from_double_booking_idx = None

                        # If a class to modify is selected, show the form for its reassignment
                        if st.session_state.class_to_modify_from_double_booking_idx is not None:
                            class_to_modify_details = st.session_state.generated_schedule_df.loc[st.session_state.class_to_modify_from_double_booking_idx]
                            
                            st.markdown(f"**Modifying:** {class_to_modify_details['Subject Code']} for Section {class_to_modify_details['Section']}")
                            
                            with st.form(key=f"tdb_resolve_form_{conflict_original_idx}_{st.session_state.class_to_modify_from_double_booking_idx}"):
                                st.write("New Assignment Options (leave teacher/room/time same if not changing that aspect):")
                                
                                # Get Specialized Teachers for this subject
                                required_spec_for_class = st.session_state.subjects_df[st.session_state.subjects_df['Subject Code'] == class_to_modify_details['Subject Code']]['Required Specialization'].iloc[0]
                                
                                tdb_teacher_options = ["Keep Original Teacher"] + sorted([
                                    name for name, details in st.session_state.parsed_instructors.items() 
                                    if required_spec_for_class in details['specializations'] and name != class_to_modify_details['Instructor'] # Exclude current teacher if changing
                                ])
                                new_teacher = st.selectbox("New Teacher (Optional):", tdb_teacher_options, key=f"tdb_teacher_{conflict_original_idx}")

                                # Get Suitable Rooms
                                tdb_room_options = ["Keep Original Room"] + sorted([
                                    name for name, room_slots in st.session_state.parsed_rooms.items()
                                    if any(details['capacity'] >= class_to_modify_details['Students'] for details in room_slots.values()) and name != class_to_modify_details['Room']
                                ])
                                new_room = st.selectbox("New Room (Optional):", tdb_room_options, key=f"tdb_room_{conflict_original_idx}")
                                
                                # Select New Day and Time Slot
                                new_day = st.selectbox("New Day (Optional - if changing time):", ["Keep Original Day"] + DAYS_ORDER, key=f"tdb_day_{conflict_original_idx}")
                                new_time_slot = st.selectbox("New Time Slot (Optional - if changing time):", ["Keep Original Time Slot"] + TIME_SLOTS_ORDER_24HR, key=f"tdb_time_{conflict_original_idx}")

                                submitted_tdb_fix = st.form_submit_button("Attempt to Apply Changes")

                                if submitted_tdb_fix:
                                    # --- Logic to apply TDB fix (Phase 2 for this conflict type) ---
                                    st.session_state.manual_assignment_feedback = None
                                    
                                    # Determine the actual values to use for the modified class
                                    final_teacher = new_teacher if new_teacher != "Keep Original Teacher" else class_to_modify_details['Instructor']
                                    final_room = new_room if new_room != "Keep Original Room" else class_to_modify_details['Room']
                                    final_day = new_day.upper() if new_day != "Keep Original Day" else class_to_modify_details['Day'].upper()
                                    final_time_slot = new_time_slot if new_time_slot != "Keep Original Time Slot" else class_to_modify_details['Time Slot']

                                    # Check if anything actually changed
                                    if final_teacher == class_to_modify_details['Instructor'] and \
                                       final_room == class_to_modify_details['Room'] and \
                                       final_day == class_to_modify_details['Day'].upper() and \
                                       final_time_slot == class_to_modify_details['Time Slot']:
                                        st.warning("No changes selected. Please choose a new teacher, room, or time to resolve the conflict.")
                                        st.session_state.manual_assignment_feedback = "No changes selected."
                                    else:
                                        # Create details for the MODIFIED class entry
                                        modified_class_entry = class_to_modify_details.to_dict() # Start with original
                                        modified_class_entry['Instructor'] = final_teacher
                                        modified_class_entry['Room'] = final_room
                                        modified_class_entry['Day'] = final_day
                                        modified_class_entry['Time Slot'] = final_time_slot
                                        modified_class_entry['Assignment Type'] = 'Manual (TDB Fix)'
                                        
                                        # Create a TEMPORARY schedule WITHOUT the class we are trying to move
                                        temp_schedule_df = st.session_state.generated_schedule_df.drop(index=st.session_state.class_to_modify_from_double_booking_idx)
                                        
                                        # Check if the NEW placement conflicts with the REST of the schedule
                                        new_placement_conflicts = check_manual_assignment_conflicts(
                                            temp_schedule_df,
                                            modified_class_entry # Check the new proposed slot
                                        )

                                        if not new_placement_conflicts:
                                            # Update the original DataFrame at the specific index
                                            for col, val in modified_class_entry.items():
                                                st.session_state.generated_schedule_df.loc[st.session_state.class_to_modify_from_double_booking_idx, col] = val
                                            
                                            # Remove the original "Teacher Double Booked" conflict
                                            st.session_state.conflicts.pop(conflict_original_idx)
                                            
                                            feedback_msg = (f"SUCCESS: Moved {class_to_modify_details['Subject Code']} for Sec {class_to_modify_details['Section']}. "
                                                            f"New: {final_teacher}, {final_room}, {final_day} {final_time_slot}.")
                                            st.success(feedback_msg)
                                            st.session_state.manual_assignment_feedback = feedback_msg
                                            st.session_state.selected_conflict_to_resolve_idx = None # Clear main selection
                                            st.session_state.class_to_modify_from_double_booking_idx = None # Clear sub-selection
                                            st.rerun()
                                        else:
                                            error_msg = "COULD NOT APPLY CHANGES - New placement creates conflicts:\n"
                                            for c_msg in new_placement_conflicts: error_msg += f"- {c_msg}\n"
                                            st.error(error_msg)
                                            st.session_state.manual_assignment_feedback = error_msg
                    else: # No class selected to modify from the TDB conflict
                        if selected_class_str_to_modify != "Select a class...": # if something was selected but became invalid
                             st.warning("Please select a valid class to modify from the list above.")
                             st.session_state.class_to_modify_from_double_booking_idx = None


                # Add stubs for other conflict types later
                # elif st.session_state.selected_conflict_type == 'Room Double Booked (Post-Check)':
                #     st.info("Resolution for Room Double Bookings - To be implemented.")

        # General feedback display (if any)
        if st.session_state.manual_assignment_feedback and not (submitted_unscheduled_fix or (locals().get('submitted_tdb_fix') and submitted_tdb_fix)):
             st.info(f"Last operation feedback: {st.session_state.manual_assignment_feedback}")


    elif st.session_state.generated_schedule_df is not None:
        st.success("No conflicts or issues were reported by the scheduler!")
    else:
        st.info("Scheduler has not been run yet (Tab 2), or no conflicts were generated to resolve.")
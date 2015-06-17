ALTER TABLE canvas_school_template ADD (is_default NUMBER DEFAULT 0 NOT NULL);
ALTER TABLE bulk_canvas_course_crtn_job ADD (template_canvas_course_id NUMBER);

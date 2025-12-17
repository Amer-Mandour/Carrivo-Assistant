-- بيانات أولية للأسئلة الشائعة

-- أسئلة باللهجة المصرية
INSERT INTO faq (question_egyptian, answer_egyptian, question_ar, answer_ar, question_en, answer_en, category, tags) VALUES
('ازاي ابدأ في البرمجة؟', 'هتبدأ بلغة سهلة زى Python، وتعمل مشاريع بسيطة، ومتستعجلش على نفسك. كلو خطوة خطوة 🚶‍♂️', 'كيف أبدأ في تعلم البرمجة؟', 'ابدأ بلغة سهلة مثل Python، قم بعمل مشاريع بسيطة، وكن صبوراً. التعلم عملية تراكمية', 'How do I start learning programming?', 'Start with an easy language like Python, build simple projects, and be patient. Learning is cumulative', 'مبتدئ', '{برمجة, بداية, Python}'),

('ايه أفضل لغة برمجة للمبتدئين؟', 'Python أحسن حاجة ليك علشان سهلة وكتير بيستخدموها في مجالات مختلفة. وبعدين تروح على حاجة تانية حسب اللي عايز تعمله 🐍', 'ما هي أفضل لغة برمجة للمبتدئين؟', 'Python هي الخيار الأفضل بسبب سهولتها وتعدد استخداماتها. يمكنك الانتقال فيما بعد للغات أخرى حسب احتياجاتك', 'What is the best programming language for beginners?', 'Python is the best choice due to its simplicity and versatility. You can move to other languages later based on your needs', 'برمجة', '{لغات, Python, مبتدئ}'),

('الفرونت اند والباك اند ايه الفرق بينهم؟', 'الفرونت اند ده اللي بتشوفه في الموقع (شكل وتصميم)، والباك اند ده اللي بيتعمل ورا الكواليس (داتا ولوجك). الواحد مكمل للتاني 👨‍💻', 'ما الفرق بين Frontend و Backend؟', 'Frontend هو ما تراه في الموقع (التصميم والمظهر)، وBackend هو ما يعمل خلف الكواليس (البيانات والمنطق). كلاهما مكمل للآخر', 'What is the difference between Frontend and Backend?', 'Frontend is what you see on the website (design and appearance), Backend is what works behind the scenes (data and logic). They complement each other', 'ويب', '{فرونت اند, باك اند, تطوير}'),

('عايز اشتغل فريلانس، ازاي ابدأ؟', 
 'هتبدأ بمعرفة حاجة واحدة كويس (زي مثلاً تطوير ويب)، وتعمل بورتفوليو حلو من مشاريعك، وتشتغل على ال soft skills بتاعتك (اتصال وتنظيم وقت). LinkedIn و Upwork أحسن أماكن للبداية 💼',
 'كيف أبدأ العمل الحر (فريلانس) في البرمجة؟',
 'ابدأ بتخصص واحد تتقنه جيداً (مثل تطوير الويب)، أنشئ بورتفوليو قوي من مشاريعك، وطور مهاراتك الناعمة (التواصل وإدارة الوقت). LinkedIn و Upwork من أفضل المنصات للبداية',
 'How do I start freelancing in programming?',
 'Start with one specialization you master well (like web development), build a strong portfolio of your projects, and develop your soft skills (communication and time management). LinkedIn and Upwork are great platforms to start',
 'مهني', '{فريلانس, عمل حر, وظيفة}'),

('HTML و CSS و JavaScript ايه العلاقة بينهم؟',
 'تخيل الموقع بيت: HTML هو الهيكل والجدران 🏗️، CSS هو الديكور والدهانات 🎨، وJavaScript هو الكهربا والسباكة اللي تخلي البيت يعمل ⚡',
 'ما العلاقة بين HTML و CSS و JavaScript؟',
 'تخيل الموقع كمنزل: HTML هو الهيكل والجدران، CSS هو الديكور والألوان، وJavaScript هو الكهرباء والسباكة التي تجعل المنزل يعمل',
 'What is the relationship between HTML, CSS and JavaScript?',
 'Imagine the website as a house: HTML is the structure and walls, CSS is the decoration and paint, and JavaScript is the electricity and plumbing that make the house work',
 'ويب', '{HTML, CSS, JavaScript, أساسيات}');

-- مسارات تعليمية
INSERT INTO roadmaps (slug, title_ar, title_en, description_ar, description_en, category, difficulty, estimated_hours, tags, source_url) VALUES
('frontend-developer', 'مطور واجهات أمامية', 'Frontend Developer', 'مسار متكامل لتعلم تطوير واجهات المستخدم الحديثة باستخدام HTML, CSS, و JavaScript', 'Complete path to learn modern frontend development using HTML, CSS, and JavaScript', 'تطوير الويب', 'مبتدئ', 300, '{HTML, CSS, JavaScript, React, فرونت اند}', 'https://roadmap.sh/frontend'),

('backend-developer', 'مطور خوادم', 'Backend Developer', 'تعلم برمجة الخوادم، قواعد البيانات، وبناء APIs باستخدام Node.js أو Python', 'Learn server programming, databases, and building APIs using Node.js or Python', 'تطوير الويب', 'متوسط', 400, '{Node.js, Python, Database, API, باك اند}', 'https://roadmap.sh/backend'),

('fullstack-developer', 'مطور كامل المهارات', 'Full Stack Developer', 'تعلم كل من Frontend و Backend لتصبح مطوراً كاملاً قادراً على بناء تطبيقات كاملة', 'Learn both Frontend and Backend to become a full developer capable of building complete applications', 'تطوير الويب', 'متوسط', 600, '{React, Node.js, Database, Full Stack}', 'https://roadmap.sh/full-stack'),

('android-developer', 'مطور تطبيقات أندرويد', 'Android Developer', 'تعلم تطوير تطبيقات Android باستخدام Kotlin أو Java', 'Learn Android app development using Kotlin or Java', 'تطبيقات الموبايل', 'مبتدئ', 350, '{Kotlin, Java, Android, Mobile}', 'https://roadmap.sh/android');
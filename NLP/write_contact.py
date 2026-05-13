with open(r'templates/contact.html', 'w', encoding='utf-8') as f:
    f.write("""\
{%- extends "base.html" %}
{% block title %}Contact Developer — CrisisAI Sentinel{% endblock %}

{% block content %}
<div class="page-header">
  <div class="page-title-group">
    <h1 class="page-title contact-name">Karthik</h1>
    <p class="page-subtitle">AI &amp; ML Enthusiast &bull; Software Developer</p>
  </div>
</div>

<div class="contact-section">

  <div class="contact-card education-card">
    <h2 class="section-heading">&#127891; Education Details</h2>
    <div class="edu-item">
      <h3>Class 10</h3>
      <p><strong>Board:</strong> Board of Secondary Education</p>
      <p><strong>School:</strong> Please update your school name here</p>
      <p><strong>Year of Passing:</strong> Please update year here</p>
      <p><strong>Percentage/CGPA:</strong> Please update score here</p>
    </div>
  </div>

  <div class="contact-grid">
    <div class="contact-info">
      <h2 class="section-heading">Let's Connect &amp; Collaborate</h2>
      <p class="contact-desc">
        I'm open to internship opportunities, collaborative projects, and research in AI/ML and software development.
      </p>
      <ul class="contact-links">
        <li>
          <span class="c-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg></span>
          <a href="mailto:karthik@gmail.com">karthik@gmail.com</a>
        </li>
        <li>
          <span class="c-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.19 14a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"></path></svg></span>
          <a href="tel:+918008663168">+91-8008663168</a>
        </li>
        <li>
          <span class="c-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg></span>
          <a href="https://github.com/Karthik" target="_blank">github.com/Karthik</a>
        </li>
        <li>
          <span class="c-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg></span>
          <a href="https://linkedin.com/in/karthik" target="_blank">linkedin.com/in/karthik</a>
        </li>
      </ul>
    </div>

    <div class="contact-form-wrapper">
      <form class="contact-form" onsubmit="event.preventDefault(); alert('Message sent!');">
        <div class="form-group">
          <label>YOUR NAME</label>
          <input type="text" placeholder="Your name here" required />
        </div>
        <div class="form-group">
          <label>EMAIL ADDRESS</label>
          <input type="email" placeholder="your@email.com" required />
        </div>
        <div class="form-group">
          <label>MESSAGE</label>
          <textarea placeholder="Hello Karthik! I'd like to connect about..." required></textarea>
        </div>
        <button type="submit" class="btn-send">
          <span class="btn-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg></span>
          Send Message
        </button>
      </form>
    </div>
  </div>
</div>
{% endblock %}
""")
print("OK")

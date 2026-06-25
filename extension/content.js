function extractJobData() {
  const url = window.location.href;
  let data = {
    title: "",
    description: "",
    company_profile: "",
    requirements: "",
    benefits: "",
    telecommuting: 0,
    has_company_logo: 0,
    has_questions: 0,
    employment_type: "unknown",
    required_experience: "unknown",
    has_salary: 0
  };

  if (url.includes("linkedin.com")) {
    data.title = document.querySelector(".job-details-jobs-unified-top-card__job-title")?.innerText || "";
    data.description = document.querySelector('[data-testid="expandable-text-box"]')?.innerText || "";
    const descLower = data.description.toLowerCase;
    data.has_salary = /₹|\$|salary|stipend|lpa|per month|per annum/.test(descLower) ? 1 : 0;
    data.telecommuting = /remote|work from home|virtual/.test(descLower) ? 1 : 0;
    data.has_questions = /apply now|fill the form|google form|application form/.test(descLower) ? 0 : 1;
    data.has_company_logo = document.querySelector("img[alt*='Company logo']") ? 1 : 0;
    const hasEmojis = /[\u{1F300}-\u{1FFFF}]/u.test(data.description);
    data.has_emojis = hasEmojis ? 1 : 0;
  } else if (url.includes("naukri.com")) {
    data.title = document.querySelector(".job-title")?.innerText || "";
    data.description = document.querySelector(".job-desc")?.innerText || "";
    data.has_company_logo = document.querySelector(".comp-logo") ? 1 : 0;
  } else if (url.includes("internshala.com")) {
    data.title = document.querySelector(".profile")?.innerText || "";
    data.description = document.querySelector(".internship_details")?.innerText || "";
    data.has_company_logo = document.querySelector(".internship_logo") ? 1 : 0;
  } else if (url.includes("indeed.com")) {
    data.title = document.querySelector('[data-testid="jobsearch-JobInfoHeader-title"]')?.innerText || "";
    data.description = document.querySelector("#jobDescriptionText")?.innerText || "";
  }

  return data;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "extractJob") {
    sendResponse(extractJobData());
  }
});
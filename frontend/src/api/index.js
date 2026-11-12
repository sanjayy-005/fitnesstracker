import api from "./client";

/** Every backend endpoint the app uses, grouped by feature. */

// Remove empty filter values so they are not sent as "?search=&status=".
const clean = (params = {}) =>
  Object.fromEntries(Object.entries(params).filter(([, value]) => value !== "" && value !== null && value !== undefined));

const unwrap = (request) => request.then((response) => response.data);

function crud(path) {
  return {
    list: (params) => unwrap(api.get(`/${path}/`, { params: clean(params) })),
    get: (id) => unwrap(api.get(`/${path}/${id}/`)),
    create: (data) => unwrap(api.post(`/${path}/`, data)),
    update: (id, data) => unwrap(api.patch(`/${path}/${id}/`, data)),
    remove: (id) => unwrap(api.delete(`/${path}/${id}/`)),
  };
}

export const authApi = {
  login: (username, password) => unwrap(api.post("/auth/login/", { username, password })),
  logout: (refresh) => unwrap(api.post("/auth/logout/", { refresh })),
  me: () => unwrap(api.get("/auth/me/")),
};

export const dashboardApi = {
  get: () => unwrap(api.get("/dashboard/")),
};

export const usersApi = crud("auth/users");
export const membersApi = crud("members");
export const plansApi = crud("plans");

export const trainersApi = {
  ...crud("trainers"),
  members: (id) => unwrap(api.get(`/trainers/${id}/members/`)),
  assign: (id, memberIds) => unwrap(api.post(`/trainers/${id}/assign/`, { member_ids: memberIds })),
  unassign: (id, memberIds) => unwrap(api.post(`/trainers/${id}/unassign/`, { member_ids: memberIds })),
};

export const membershipsApi = {
  list: crud("memberships").list,
  create: crud("memberships").create,
  remove: crud("memberships").remove,
  renew: (id, data) => unwrap(api.post(`/memberships/${id}/renew/`, data)),
  cancel: (id) => unwrap(api.post(`/memberships/${id}/cancel/`)),
};

export const paymentsApi = {
  ...crud("payments"),
  summary: (params) => unwrap(api.get("/payments/summary/", { params: clean(params) })),
  receipt: (id) => unwrap(api.get(`/payments/${id}/receipt/`)),
};

export const attendanceApi = {
  list: crud("attendance").list,
  remove: crud("attendance").remove,
  checkIn: (memberId) => unwrap(api.post("/attendance/check-in/", { member: memberId })),
  checkOut: (id) => unwrap(api.post(`/attendance/${id}/check-out/`)),
  report: (days) => unwrap(api.get("/attendance/report/", { params: { days } })),
};

export const portalApi = {
  profile: () => unwrap(api.get("/portal/profile/")),
  memberships: () => unwrap(api.get("/portal/memberships/")),
  attendance: (params) => unwrap(api.get("/portal/attendance/", { params: clean(params) })),
};

export const nutritionApi = {
  scans: {
    list: (params) => unwrap(api.get("/nutrition/scans/", { params: clean(params) })),
    get: (id) => unwrap(api.get(`/nutrition/scans/${id}/`)),
    upload: (formData) =>
      unwrap(
        api.post("/nutrition/scans/", formData, {
          timeout: 120000,
        })
      ),
    confirm: (id, data) => unwrap(api.post(`/nutrition/scans/${id}/confirm/`, data)),
  },
  entries: {
    list: (params) => unwrap(api.get("/nutrition/entries/", { params: clean(params) })),
    get: (id) => unwrap(api.get(`/nutrition/entries/${id}/`)),
    remove: (id) => unwrap(api.delete(`/nutrition/entries/${id}/`)),
    manual: (data) => unwrap(api.post("/nutrition/entries/manual/", data)),
  },
  summary: (params) => unwrap(api.get("/nutrition/summary/", { params: clean(params) })),
  consent: () => unwrap(api.post("/nutrition/consent/")),
  status: () => unwrap(api.get("/nutrition/status/")),
};

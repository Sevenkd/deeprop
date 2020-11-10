import { Effect, Reducer } from 'umi';

import { queryCurrent, query as queryUsers } from '@/services/user';

interface CurrentUser {
  userId?: number;
  doctorName?: string;
  hospitalId?: number;
  hospitalName?: string;
  role?: string;
  [otherKey: string]: any;
}

interface UserModelState {
  currentUser?: CurrentUser;
}

interface UserModelType {
  namespace: 'user';
  state: UserModelState;
  effects: {
    loginUser: Effect;
    logoutUser: Effect;
  };
  reducers: {
    saveUserInfo: Reducer<UserModelState>;
    deleteUserInfo: Reducer;
  };
}

const UserModel: UserModelType = {
  namespace: 'user',

  state: {
    currentUser: {},
  },

  effects: {

    *loginUser(_, { call, put }) {
      const response = yield call(queryUsers);

      yield put({
        type: 'saveUserInfo',
        payload: response,
      });
    },

    *logoutUser(_, { call, put }) {
      const response = yield call(queryCurrent);

      yield put({ type: 'deleteUserInfo' });
    },

  },

  reducers: {

    saveUserInfo(state, action) {
      return { ...state, currentUser: action.payload };
    },

    deleteUserInfo(state) {
      return { ...state, currentUser: {} };
    },

  },
};

export default UserModel;
export { CurrentUser, UserModelState, UserModelType };

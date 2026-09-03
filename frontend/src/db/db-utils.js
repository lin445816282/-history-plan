// /src/db/db-utils.js
// IndexedDB 通用操作封装

import { DB_CONFIG, MODELS } from './db-schema.js';

export class HistoryPlanDB {
  constructor() {
    this.db = null;
    this.ready = this.init();
  }

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_CONFIG.name, DB_CONFIG.version);
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        const stores = DB_CONFIG.stores;
        
        // 创建/升级所有Store
        Object.keys(stores).forEach(storeName => {
          if (!db.objectStoreNames.contains(storeName)) {
            const config = stores[storeName];
            const store = db.createObjectStore(storeName, { 
              keyPath: config.keyPath, 
              autoIncrement: config.autoIncrement 
            });
            config.indexes.forEach(idx => {
              store.createIndex(idx.name, idx.keyPath);
            });
          }
        });
      };

      request.onsuccess = (event) => {
        this.db = event.target.result;
        resolve(this.db);
      };

      request.onerror = (event) => {
        reject(event.target.error);
      };
    });
  }

  // 通用CRUD

  async add(storeName, data) {
    await this.ready;
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.add(data);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async get(storeName, id) {
    await this.ready;
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(storeName, 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.get(id);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async getAll(storeName) {
    await this.ready;
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(storeName, 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async getByIndex(storeName, indexName, value) {
    await this.ready;
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(storeName, 'readonly');
      const store = transaction.objectStore(storeName);
      const index = store.index(indexName);
      const request = index.getAll(value);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async update(storeName, data) {
    await this.ready;
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.put(data);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async delete(storeName, id) {
    await this.ready;
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.delete(id);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async deleteByIndex(storeName, indexName, value) {
    await this.ready;
    const items = await this.getByIndex(storeName, indexName, value);
    const ids = items.map(item => item.id);
    const transaction = this.db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const promises = ids.map(id => {
      return new Promise((resolve, reject) => {
        const request = store.delete(id);
        request.onsuccess = resolve;
        request.onerror = reject;
      });
    });
    await Promise.all(promises);
    return ids.length;
  }

  // 级联删除档案（含快照、复盘、待办）
  async cascadeDeleteProfile(profileId) {
    await this.ready;
    const snapshotIds = await this.getByIndex('snapshots', 'by_profileId', profileId);
    const snapshotIdList = snapshotIds.map(s => s.id);
    
    // 删除关联快照
    for (const sid of snapshotIdList) {
      await this.delete('snapshots', sid);
    }
    
    // 删除关联复盘
    const reviews = await this.getByIndex('reviews', 'by_profileId', profileId);
    for (const r of reviews) {
      await this.delete('reviews', r.id);
    }
    
    // 删除关联待办
    const todos = await this.getByIndex('todos', 'by_profileId', profileId);
    for (const t of todos) {
      await this.delete('todos', t.id);
    }
    
    // 删除档案
    await this.delete('profiles', profileId);
    return {
      snapshotsDeleted: snapshotIdList.length,
      reviewsDeleted: reviews.length,
      todosDeleted: todos.length
    };
  }

  // 备份导出全部数据
  async exportAllData() {
    await this.ready;
    const profiles = await this.getAll('profiles');
    const snapshots = await this.getAll('snapshots');
    const reviews = await this.getAll('reviews');
    const todos = await this.getAll('todos');
    
    return {
      version: '1.7.0',
      exportedAt: new Date().toISOString(),
      profiles,
      snapshots,
      reviews,
      todos
    };
  }

  // 备份导入（合并策略）
  async importAllData(data) {
    await this.ready;
    const results = { added: 0, merged: 0, errors: 0 };
    
    // 导入profiles（ID冲突时覆盖）
    for (const profile of data.profiles || []) {
      try {
        const existing = await this.get('profiles', profile.id);
        if (existing) {
          await this.update('profiles', profile);
          results.merged++;
        } else {
          await this.add('profiles', profile);
          results.added++;
        }
      } catch (e) {
        results.errors++;
        console.error('导入profile失败:', e);
      }
    }
    
    // 类似处理snapshots, reviews, todos...
    // (完整代码略，逻辑同上)
    
    return results;
  }
}
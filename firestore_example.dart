import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

class FirestoreService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Get a collection reference
  CollectionReference collection(String path) {
    return _firestore.collection(path);
  }

  // Get a document reference
  DocumentReference document(String path) {
    return _firestore.doc(path);
  }

  // Add a document to a collection
  Future<DocumentReference> addDocument(
    String collection,
    Map<String, dynamic> data,
  ) async {
    return await _firestore.collection(collection).add(data);
  }

  // Set a document with a specific ID
  Future<void> setDocument(
    String path,
    Map<String, dynamic> data, {
    bool merge = true,
  }) async {
    return await _firestore.doc(path).set(data, SetOptions(merge: merge));
  }

  // Update a document
  Future<void> updateDocument(String path, Map<String, dynamic> data) async {
    return await _firestore.doc(path).update(data);
  }

  // Delete a document
  Future<void> deleteDocument(String path) async {
    return await _firestore.doc(path).delete();
  }

  // Get a document
  Future<DocumentSnapshot> getDocument(String path) async {
    return await _firestore.doc(path).get();
  }

  // Get a collection
  Stream<QuerySnapshot> getCollection(String path) {
    return _firestore.collection(path).snapshots();
  }

  // Query a collection
  Stream<QuerySnapshot> queryCollection(
    String path, {
    required List<QueryCondition> conditions,
    List<QueryOrder>? orders,
    int? limit,
  }) {
    Query query = _firestore.collection(path);

    // Apply where conditions
    for (var condition in conditions) {
      query = query.where(
        condition.field,
        isEqualTo: condition.isEqualTo,
        isNotEqualTo: condition.isNotEqualTo,
        isLessThan: condition.isLessThan,
        isLessThanOrEqualTo: condition.isLessThanOrEqualTo,
        isGreaterThan: condition.isGreaterThan,
        isGreaterThanOrEqualTo: condition.isGreaterThanOrEqualTo,
        arrayContains: condition.arrayContains,
        arrayContainsAny: condition.arrayContainsAny,
        whereIn: condition.whereIn,
        whereNotIn: condition.whereNotIn,
      );
    }

    // Apply order
    if (orders != null) {
      for (var order in orders) {
        query = query.orderBy(order.field, descending: order.descending);
      }
    }

    // Apply limit
    if (limit != null) {
      query = query.limit(limit);
    }

    return query.snapshots();
  }
}

// Helper classes
class QueryCondition {
  final String field;
  final dynamic isEqualTo;
  final dynamic isNotEqualTo;
  final dynamic isLessThan;
  final dynamic isLessThanOrEqualTo;
  final dynamic isGreaterThan;
  final dynamic isGreaterThanOrEqualTo;
  final dynamic arrayContains;
  final List<dynamic>? arrayContainsAny;
  final List<dynamic>? whereIn;
  final List<dynamic>? whereNotIn;

  QueryCondition({
    required this.field,
    this.isEqualTo,
    this.isNotEqualTo,
    this.isLessThan,
    this.isLessThanOrEqualTo,
    this.isGreaterThan,
    this.isGreaterThanOrEqualTo,
    this.arrayContains,
    this.arrayContainsAny,
    this.whereIn,
    this.whereNotIn,
  });
}

class QueryOrder {
  final String field;
  final bool descending;

  QueryOrder({required this.field, this.descending = false});
}

// Example UI to display a list of items from Firestore
class FirestoreListExample extends StatelessWidget {
  final FirestoreService _firestoreService = FirestoreService();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Firestore Items')),
      body: StreamBuilder<QuerySnapshot>(
        stream: _firestoreService.getCollection('items'),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }

          if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
            return Center(child: Text('No items found'));
          }

          return ListView.builder(
            itemCount: snapshot.data!.docs.length,
            itemBuilder: (context, index) {
              var doc = snapshot.data!.docs[index];
              var data = doc.data() as Map<String, dynamic>;

              return ListTile(
                title: Text(data['name'] ?? 'No name'),
                subtitle: Text(data['description'] ?? 'No description'),
                trailing: IconButton(
                  icon: Icon(Icons.delete),
                  onPressed: () {
                    _firestoreService.deleteDocument('items/${doc.id}');
                  },
                ),
                onTap: () {
                  // Navigate to item details or edit screen
                },
              );
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        child: Icon(Icons.add),
        onPressed: () {
          // Add a new item
          _firestoreService.addDocument('items', {
            'name': 'New Item',
            'description': 'A description for the new item',
            'createdAt': FieldValue.serverTimestamp(),
          });
        },
      ),
    );
  }
}

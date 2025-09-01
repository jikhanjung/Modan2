"""
Controller layer for Modan2 application.
Handles business logic and coordinates between View and Model.
"""
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal

import MdModel
import MdStatistics
import MdUtils as mu


class ModanController(QObject):
    """Main controller - handles business logic."""
    
    # Signals for View communication
    dataset_created = pyqtSignal(object)        # MdDataset
    dataset_updated = pyqtSignal(object)        # MdDataset
    dataset_deleted = pyqtSignal(int)           # dataset_id
    
    object_added = pyqtSignal(object)           # MdObject
    object_updated = pyqtSignal(object)         # MdObject
    object_deleted = pyqtSignal(int)            # object_id
    
    analysis_started = pyqtSignal(str)          # analysis_type
    analysis_progress = pyqtSignal(int)         # progress_percentage
    analysis_completed = pyqtSignal(object)     # MdAnalysis
    analysis_failed = pyqtSignal(str)           # error_message
    
    error_occurred = pyqtSignal(str)            # error_message
    warning_occurred = pyqtSignal(str)          # warning_message
    info_message = pyqtSignal(str)              # info_message
    
    def __init__(self, view=None):
        """Initialize controller.
        
        Args:
            view: Reference to main window (optional for testing)
        """
        super().__init__()
        self.view = view
        self.logger = logging.getLogger(__name__)
        
        # Current state
        self.current_dataset: Optional[MdModel.MdDataset] = None
        self.current_object: Optional[MdModel.MdObject] = None
        self.current_analysis: Optional[MdModel.MdAnalysis] = None
        
        # Processing flags
        self._processing = False
    
    # ========== Dataset Operations ==========
    
    def create_dataset(self, name: str, desc: str, dimension: int, 
                      landmark_count: int, **kwargs) -> Optional[MdModel.MdDataset]:
        """Create a new dataset.
        
        Args:
            name: Dataset name
            desc: Dataset description
            dimension: 2 or 3
            landmark_count: Number of landmarks
            **kwargs: Additional parameters
            
        Returns:
            Created dataset or None if failed
        """
        try:
            self.logger.info(f"Creating dataset: {name} ({dimension}D, {landmark_count} landmarks)")
            
            # Validate inputs
            if not name.strip():
                raise ValueError("Dataset name cannot be empty")
            
            if dimension not in [2, 3]:
                raise ValueError("Dimension must be 2 or 3")
            
            if landmark_count < 0:
                raise ValueError("Landmark count must be non-negative")
            
            # Check for duplicate name
            existing = MdModel.MdDataset.select().where(
                MdModel.MdDataset.dataset_name == name
            )
            if existing.exists():
                raise ValueError(f"Dataset with name '{name}' already exists")
            
            # Create dataset
            dataset = MdModel.MdDataset.create(
                dataset_name=name,
                dataset_desc=desc,
                dimension=dimension,
                landmark_count=landmark_count,
                **kwargs
            )
            
            self.dataset_created.emit(dataset)
            self.info_message.emit(f"Dataset '{name}' created successfully")
            return dataset
            
        except Exception as e:
            self.logger.error(f"Failed to create dataset: {e}")
            self.error_occurred.emit(f"Failed to create dataset: {str(e)}")
            return None
    
    def update_dataset(self, dataset_id: int, **updates) -> bool:
        """Update dataset properties.
        
        Args:
            dataset_id: ID of dataset to update
            **updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            dataset = MdModel.MdDataset.get_by_id(dataset_id)
            
            for field, value in updates.items():
                if hasattr(dataset, field):
                    setattr(dataset, field, value)
                else:
                    self.logger.warning(f"Unknown dataset field: {field}")
            
            dataset.save()
            self.dataset_updated.emit(dataset)
            self.info_message.emit(f"Dataset '{dataset.dataset_name}' updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update dataset {dataset_id}: {e}")
            self.error_occurred.emit(f"Failed to update dataset: {str(e)}")
            return False
    
    def delete_dataset(self, dataset_id: int) -> bool:
        """Delete dataset and all its objects.
        
        Args:
            dataset_id: ID of dataset to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            dataset = MdModel.MdDataset.get_by_id(dataset_id)
            dataset_name = dataset.dataset_name
            
            self.logger.info(f"Deleting dataset: {dataset_name}")
            
            # Delete all related objects first
            objects_deleted = 0
            for obj in dataset.object_list:
                obj.delete_instance(recursive=True)
                objects_deleted += 1
            
            # Delete all related analyses
            analyses_deleted = 0
            # Check if dataset has analyses (backref may be 'analysis_set' or similar)
            if hasattr(dataset, 'analysis_set'):
                for analysis in dataset.analysis_set:
                    analysis.delete_instance()
                    analyses_deleted += 1
            elif hasattr(dataset, 'analyses'):
                for analysis in dataset.analyses:
                    analysis.delete_instance()
                    analyses_deleted += 1
            
            # Delete the dataset itself
            dataset.delete_instance()
            
            # Clear current selection if it was the deleted dataset
            if self.current_dataset and self.current_dataset.id == dataset_id:
                self.current_dataset = None
                self.current_object = None
                self.current_analysis = None
            
            self.dataset_deleted.emit(dataset_id)
            self.info_message.emit(
                f"Dataset '{dataset_name}' deleted "
                f"({objects_deleted} objects, {analyses_deleted} analyses)"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete dataset {dataset_id}: {e}")
            self.error_occurred.emit(f"Failed to delete dataset: {str(e)}")
            return False
    
    def set_current_dataset(self, dataset: Optional[MdModel.MdDataset]):
        """Set currently selected dataset.
        
        Args:
            dataset: Dataset to select or None to clear selection
        """
        self.logger.debug(f"set_current_dataset called with: {dataset} (type: {type(dataset)})")
        self.current_dataset = dataset
        self.current_object = None  # Clear object selection
        
        if dataset:
            self.logger.debug(f"Current dataset set to: {dataset.dataset_name}")
        else:
            self.logger.debug("Dataset selection cleared")
    
    # ========== Object Operations ==========
    
    def create_object(self, object_name: str = None, object_desc: str = "") -> MdModel.MdObject:
        """Create a new empty object.
        
        Args:
            object_name: Name for the new object (auto-generated if None)
            object_desc: Description for the object
            
        Returns:
            Created object
        """
        self.logger.debug(f"create_object called, current_dataset: {self.current_dataset}")
        if not self.current_dataset:
            self.logger.error(f"No current dataset: {self.current_dataset}")
            self.error_occurred.emit("Please select a dataset first")
            return None
        
        try:
            # Generate name if not provided
            if not object_name:
                existing_count = len(self.current_dataset.object_list)
                object_name = f"Object_{existing_count + 1}"
            
            # Create object
            obj = MdModel.MdObject.create(
                dataset=self.current_dataset,
                object_name=object_name,
                object_desc=object_desc,
                sequence=len(self.current_dataset.object_list) + 1
            )
            
            self.logger.info(f"Created new object: {object_name}")
            self.object_added.emit(obj)
            return obj
            
        except Exception as e:
            self.logger.error(f"Failed to create object: {e}")
            self.error_occurred.emit(f"Failed to create object: {str(e)}")
            return None
    
    def import_objects(self, file_paths: List[str]) -> List[MdModel.MdObject]:
        """Import objects from files.
        
        Args:
            file_paths: List of file paths to import
            
        Returns:
            List of successfully imported objects
        """
        if not self.current_dataset:
            self.error_occurred.emit("Please select a dataset first")
            return []
        
        if self._processing:
            self.warning_occurred.emit("Another operation is in progress")
            return []
        
        self._processing = True
        imported_objects = []
        
        try:
            self.logger.info(f"Importing {len(file_paths)} file(s)")
            
            for i, file_path in enumerate(file_paths):
                try:
                    # Update progress
                    progress = int((i / len(file_paths)) * 100)
                    self.analysis_progress.emit(progress)
                    
                    objects = self._import_single_file(file_path)
                    imported_objects.extend(objects)
                    
                except Exception as e:
                    self.logger.error(f"Failed to import {file_path}: {e}")
                    self.error_occurred.emit(f"Failed to import {Path(file_path).name}: {str(e)}")
            
            # Final progress
            self.analysis_progress.emit(100)
            
            self.info_message.emit(f"Imported {len(imported_objects)} object(s)")
            return imported_objects
            
        finally:
            self._processing = False
    
    def _import_single_file(self, file_path: str) -> List[MdModel.MdObject]:
        """Import objects from a single file.
        
        Args:
            file_path: Path to file to import
            
        Returns:
            List of imported objects
        """
        file_ext = Path(file_path).suffix.lower()
        
        self.logger.debug(f"Importing file: {file_path} (type: {file_ext})")
        
        if file_ext in ['.tps', '.nts', '.txt']:
            return self._import_landmark_file(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return [self._import_image_file(file_path)]
        elif file_ext in ['.obj', '.ply', '.stl']:
            return [self._import_3d_file(file_path)]
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def _import_landmark_file(self, file_path: str) -> List[MdModel.MdObject]:
        """Import landmarks from TPS/NTS file.
        
        Args:
            file_path: Path to landmark file
            
        Returns:
            List of created objects
        """
        try:
            # Read landmark data
            landmarks_data = mu.read_landmark_file(file_path)
            
            if not landmarks_data:
                raise ValueError("No landmarks found in file")
            
            objects = []
            for idx, (specimen_name, landmarks) in enumerate(landmarks_data):
                # Validate landmark count
                if len(landmarks) != self.current_dataset.landmark_count:
                    self.logger.warning(
                        f"Landmark count mismatch for {specimen_name}: "
                        f"expected {self.current_dataset.landmark_count}, got {len(landmarks)}"
                    )
                
                # Create object
                obj = MdModel.MdObject.create(
                    dataset=self.current_dataset,
                    object_name=specimen_name or f"{Path(file_path).stem}_{idx+1}",
                    object_desc=f"Imported from {Path(file_path).name}",
                    landmarks=landmarks
                )
                
                objects.append(obj)
                self.object_added.emit(obj)
            
            return objects
            
        except Exception as e:
            raise ValueError(f"Failed to read landmark file: {str(e)}")
    
    def _import_image_file(self, file_path: str) -> MdModel.MdObject:
        """Import image file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Created object
        """
        try:
            # Create image record
            image = MdModel.MdImage.create(
                file_path=file_path,
                dataset=self.current_dataset
            )
            
            # Create object
            obj = MdModel.MdObject.create(
                dataset=self.current_dataset,
                object_name=Path(file_path).stem,
                object_desc=f"Image imported from {Path(file_path).name}",
                image=image
            )
            
            self.object_added.emit(obj)
            return obj
            
        except Exception as e:
            raise ValueError(f"Failed to import image: {str(e)}")
    
    def _import_3d_file(self, file_path: str) -> MdModel.MdObject:
        """Import 3D model file.
        
        Args:
            file_path: Path to 3D model file
            
        Returns:
            Created object
        """
        try:
            # Convert to OBJ format if needed
            obj_path = mu.process_3d_file(file_path)
            
            # Create 3D model record
            model_3d = MdModel.MdThreeDModel.create(
                file_path=obj_path,
                dataset=self.current_dataset
            )
            
            # Create object
            obj = MdModel.MdObject.create(
                dataset=self.current_dataset,
                object_name=Path(file_path).stem,
                object_desc=f"3D model imported from {Path(file_path).name}",
                model_3d=model_3d
            )
            
            self.object_added.emit(obj)
            return obj
            
        except Exception as e:
            raise ValueError(f"Failed to import 3D model: {str(e)}")
    
    def update_object(self, object_id: int, **updates) -> bool:
        """Update object properties.
        
        Args:
            object_id: ID of object to update
            **updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            obj = MdModel.MdObject.get_by_id(object_id)
            
            for field, value in updates.items():
                if hasattr(obj, field):
                    setattr(obj, field, value)
                else:
                    self.logger.warning(f"Unknown object field: {field}")
            
            obj.save()
            self.object_updated.emit(obj)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update object {object_id}: {e}")
            self.error_occurred.emit(f"Failed to update object: {str(e)}")
            return False
    
    def delete_object(self, object_id: int) -> bool:
        """Delete object.
        
        Args:
            object_id: ID of object to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            obj = MdModel.MdObject.get_by_id(object_id)
            obj_name = obj.object_name
            
            obj.delete_instance(recursive=True)
            
            # Clear current selection if it was the deleted object
            if self.current_object and self.current_object.id == object_id:
                self.current_object = None
            
            self.object_deleted.emit(object_id)
            self.info_message.emit(f"Object '{obj_name}' deleted")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete object {object_id}: {e}")
            self.error_occurred.emit(f"Failed to delete object: {str(e)}")
            return False
    
    def set_current_object(self, obj: Optional[MdModel.MdObject]):
        """Set currently selected object.
        
        Args:
            obj: Object to select or None to clear selection
        """
        self.current_object = obj
        
        if obj:
            self.logger.debug(f"Current object set to: {obj.object_name}")
        else:
            self.logger.debug("Object selection cleared")
    
    # ========== Analysis Operations ==========
    
    def run_analysis(self, dataset=None, analysis_name="", superimposition_method="", 
                     cva_group_by=None, manova_group_by=None, **kwargs) -> Optional[MdModel.MdAnalysis]:
        """Run statistical analysis.
        
        Args:
            dataset: Dataset to analyze (defaults to current_dataset)
            analysis_name: Name for the analysis
            superimposition_method: Method for superimposition
            cva_group_by: Grouping variable for CVA
            manova_group_by: Grouping variable for MANOVA
            **kwargs: Additional parameters for backward compatibility
            
        Returns:
            Analysis result or None if failed
        """
        # Handle backward compatibility
        if isinstance(dataset, str):
            # Old signature: run_analysis(analysis_type, params)
            analysis_type = dataset
            params = analysis_name if isinstance(analysis_name, dict) else {}
            analysis_name = params.get("name", f"{analysis_type}_Analysis")
            dataset = self.current_dataset
        else:
            # New signature from UI
            if dataset:
                self.set_current_dataset(dataset)
            # Initialize params for new signature
            params = {}
        if not self.current_dataset:
            self.error_occurred.emit("Please select a dataset first")
            return None
        
        if self._processing:
            self.warning_occurred.emit("Another analysis is already running")
            return None
        
        self._processing = True
        
        try:
            if 'analysis_type' not in locals():
                analysis_type = "PCA"  # Default
            self.logger.info(f"Starting {analysis_type} analysis")
            self.analysis_started.emit(analysis_type)
            
            # Get objects with landmarks
            objects = list(self.current_dataset.object_list)
            objects_with_landmarks = []
            for obj in objects:
                obj.unpack_landmark()
                if obj.landmark_str and obj.landmark_list:
                    objects_with_landmarks.append(obj)
            
            if len(objects_with_landmarks) < 2:
                raise ValueError(f"At least 2 objects with landmarks are required for analysis (found {len(objects_with_landmarks)} objects with landmarks out of {len(objects)} total objects)")
            
            # Extract landmarks
            landmarks_data = []
            object_names = []
            for obj in objects_with_landmarks:
                landmarks_data.append(obj.landmark_list)
                object_names.append(obj.object_name)
            
            if not landmarks_data:
                raise ValueError("No objects with landmarks found")
            
            # Run analysis based on type
            self.analysis_progress.emit(25)
            
            # Run comprehensive analysis (PCA includes all three: PCA, CVA, MANOVA)
            if analysis_type.upper() == "PCA":
                pca_result = self._run_pca(landmarks_data, params)
                result = pca_result  # Primary result for compatibility
                
                # Also run CVA and MANOVA as part of comprehensive analysis
                cva_result = None
                manova_result = None
                
                self.logger.info(f"CVA group_by parameter: {cva_group_by}")
                if cva_group_by is not None:
                    try:
                        self.logger.info("Running CVA analysis alongside PCA")
                        
                        # Extract group values from objects based on cva_group_by index
                        group_values = []
                        variable_names = self.current_dataset.get_variablename_list()
                        
                        if isinstance(cva_group_by, int) and 0 <= cva_group_by < len(variable_names):
                            # cva_group_by is an index
                            for obj in objects_with_landmarks:
                                obj_model = self.current_dataset.object_list.where(MdModel.MdObject.id == obj.id).first()
                                if obj_model:
                                    variable_list = obj_model.get_variable_list()
                                    if cva_group_by < len(variable_list):
                                        group_values.append(variable_list[cva_group_by])
                                    else:
                                        group_values.append("Unknown")
                                else:
                                    group_values.append("Unknown")
                        else:
                            # cva_group_by might be a string or direct group list
                            if isinstance(cva_group_by, str):
                                self.logger.warning(f"CVA group_by is string: {cva_group_by}")
                            group_values = cva_group_by
                        
                        self.logger.info(f"CVA groups extracted: {group_values[:5]}...")  # Show first 5
                        cva_params = {"groups": group_values}
                        cva_result = self._run_cva(landmarks_data, cva_params)
                        self.logger.info("CVA analysis completed successfully")
                    except Exception as e:
                        self.logger.warning(f"CVA analysis failed: {e}")
                        import traceback
                        self.logger.warning(f"CVA error traceback: {traceback.format_exc()}")
                else:
                    self.logger.warning("CVA group_by is None - skipping CVA analysis")
                
                if manova_group_by is not None:
                    try:
                        self.logger.info("Running MANOVA analysis alongside PCA")
                        
                        # Extract group values for MANOVA (same logic as CVA)
                        manova_group_values = []
                        variable_names = self.current_dataset.get_variablename_list()
                        
                        if isinstance(manova_group_by, int) and 0 <= manova_group_by < len(variable_names):
                            # manova_group_by is an index
                            for obj in objects_with_landmarks:
                                obj_model = self.current_dataset.object_list.where(MdModel.MdObject.id == obj.id).first()
                                if obj_model:
                                    variable_list = obj_model.get_variable_list()
                                    if manova_group_by < len(variable_list):
                                        manova_group_values.append(variable_list[manova_group_by])
                                    else:
                                        manova_group_values.append("Unknown")
                                else:
                                    manova_group_values.append("Unknown")
                        else:
                            manova_group_values = manova_group_by
                            
                        self.logger.info(f"MANOVA groups extracted: {manova_group_values[:5]}...")
                        manova_params = {"groups": manova_group_values}
                        manova_result = self._run_manova(landmarks_data, manova_params)
                        self.logger.info("MANOVA analysis completed successfully")
                    except Exception as e:
                        self.logger.warning(f"MANOVA analysis failed: {e}")
                        
            elif analysis_type.upper() == "CVA":
                result = self._run_cva(landmarks_data, params)
            elif analysis_type.upper() == "MANOVA":
                result = self._run_manova(landmarks_data, params)
            elif analysis_type.upper() == "PROCRUSTES":
                result = self._run_procrustes(landmarks_data, params)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            self.analysis_progress.emit(75)
            
            # Create analysis record with JSON data
            analysis = MdModel.MdAnalysis.create(
                dataset=self.current_dataset,
                analysis_name=analysis_name or f"{analysis_type}_Analysis",
                superimposition_method=superimposition_method or "Procrustes",
                cva_group_by=cva_group_by,
                manova_group_by=manova_group_by,
                propertyname_str=self.current_dataset.propertyname_str,
                dimension=self.current_dataset.dimension,
                wireframe=self.current_dataset.wireframe,
                baseline=self.current_dataset.baseline,
                polygons=self.current_dataset.polygons
            )
            
            # Generate and save JSON data for analysis results
            try:
                import json
                
                # Generate object info JSON
                object_info_list = []
                raw_landmark_list = []
                property_len = len(self.current_dataset.get_variablename_list()) or 0
                object_list = self.current_dataset.object_list.order_by(MdModel.MdObject.sequence)
                
                for obj in object_list:
                    raw_landmark_list.append(obj.get_landmark_list())
                    object_info_list.append({
                        "id": obj.id,
                        "name": obj.object_name,
                        "sequence": obj.sequence,
                        "csize": obj.get_centroid_size(),
                        "variable_list": obj.get_variable_list()[:property_len]
                    })
                
                analysis.raw_landmark_json = json.dumps(raw_landmark_list)
                analysis.object_info_json = json.dumps(object_info_list)
                
                # Save superimposed landmark data (using current landmarks)
                superimposed_landmark_list = []
                for obj in objects_with_landmarks:
                    superimposed_landmark_list.append(obj.landmark_list)
                analysis.superimposed_landmark_json = json.dumps(superimposed_landmark_list)
                
                # Save analysis results based on type
                if analysis_type == "PCA" and result:
                    self.logger.debug(f"PCA result keys: {list(result.keys())}")
                    if 'scores' in result:
                        scores_shape = f"{len(result['scores'])}x{len(result['scores'][0]) if result['scores'] and len(result['scores']) > 0 else 0}"
                        self.logger.debug(f"PCA scores shape: {scores_shape}")
                        self.logger.debug(f"Objects with landmarks count: {len(objects_with_landmarks)}")
                        analysis.pca_analysis_result_json = json.dumps(result['scores'])
                    if 'rotation_matrix' in result:
                        analysis.pca_rotation_matrix_json = json.dumps(result['rotation_matrix'])
                    elif 'eigenvectors' in result:
                        # Fallback to eigenvectors if rotation_matrix not available
                        analysis.pca_rotation_matrix_json = json.dumps(result['eigenvectors'])
                    if 'eigenvalues' in result and 'explained_variance_ratio' in result:
                        eigenvalues_list = []
                        for i, val in enumerate(result['eigenvalues']):
                            variance_ratio = result['explained_variance_ratio'][i] if i < len(result['explained_variance_ratio']) else 0
                            eigenvalues_list.append([val, variance_ratio])
                        analysis.pca_eigenvalues_json = json.dumps(eigenvalues_list)
                
                    # Save CVA results if available (from comprehensive analysis)
                    if 'cva_result' in locals() and cva_result:
                        self.logger.info(f"Saving CVA results: keys={list(cva_result.keys())}")
                        # CVA uses 'canonical_variables' instead of 'scores'
                        if 'canonical_variables' in cva_result:
                            analysis.cva_analysis_result_json = json.dumps(cva_result['canonical_variables'])
                            self.logger.info(f"CVA canonical variables saved: {len(cva_result['canonical_variables'])} objects")
                        elif 'scores' in cva_result:
                            analysis.cva_analysis_result_json = json.dumps(cva_result['scores'])
                            self.logger.info(f"CVA scores saved: {len(cva_result['scores'])} objects")
                        
                        if 'eigenvectors' in cva_result:
                            analysis.cva_rotation_matrix_json = json.dumps(cva_result['eigenvectors'])
                        
                        if 'eigenvalues' in cva_result:
                            # CVA eigenvalues format might be different
                            if isinstance(cva_result['eigenvalues'], list):
                                # Simple eigenvalues list
                                eigenvalues_list = [[val, 0] for val in cva_result['eigenvalues']]  # No variance ratio for CVA
                                analysis.cva_eigenvalues_json = json.dumps(eigenvalues_list)
                            elif isinstance(cva_result['eigenvalues'], dict) and 'explained_variance_ratio' in cva_result:
                                # Format with variance ratios
                                cva_eigenvalues_list = []
                                for i, val in enumerate(cva_result['eigenvalues']):
                                    cva_variance_ratio = cva_result['explained_variance_ratio'][i] if i < len(cva_result['explained_variance_ratio']) else 0
                                    cva_eigenvalues_list.append([val, cva_variance_ratio])
                                analysis.cva_eigenvalues_json = json.dumps(cva_eigenvalues_list)
                    else:
                        self.logger.warning("CVA result not available for saving")
                    
                    # Save MANOVA results if available (from comprehensive analysis)
                    if 'manova_result' in locals() and manova_result:
                        analysis.manova_analysis_result_json = json.dumps(manova_result)
                
                # Save the analysis with JSON data
                analysis.save()
                self.logger.debug("Analysis results saved with JSON data")
                
            except Exception as e:
                self.logger.warning(f"Failed to generate JSON data for analysis: {e}")
                # Analysis record is still saved without JSON data
            
            self.analysis_progress.emit(100)
            self.analysis_completed.emit(analysis)
            self.info_message.emit(f"{analysis_type} analysis completed successfully")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            self.analysis_failed.emit(str(e))
            self.error_occurred.emit(f"Analysis failed: {str(e)}")
            return None
            
        finally:
            self._processing = False
    
    def _run_pca(self, landmarks_data: List[List], params: Dict[str, Any]) -> Dict[str, Any]:
        """Run PCA analysis.
        
        Args:
            landmarks_data: List of landmark arrays
            params: PCA parameters
            
        Returns:
            PCA results dictionary
        """
        self.logger.debug("Running PCA analysis")
        
        try:
            # Use existing PCA function
            pca_result = MdStatistics.do_pca_analysis(
                landmarks_data,
                n_components=params.get('n_components', None)
            )
            
            # Format results
            result = {
                'analysis_type': 'PCA',
                'n_components': pca_result.get('n_components', len(landmarks_data[0])),
                'eigenvalues': pca_result.get('eigenvalues', []),
                'eigenvectors': pca_result.get('eigenvectors', []),
                'scores': pca_result.get('scores', []),
                'explained_variance_ratio': pca_result.get('explained_variance_ratio', []),
                'cumulative_variance_ratio': pca_result.get('cumulative_variance_ratio', []),
                'mean_shape': pca_result.get('mean_shape', [])
            }
            
            return result
            
        except Exception as e:
            raise ValueError(f"PCA analysis failed: {str(e)}")
    
    def _run_cva(self, landmarks_data: List[List], params: Dict[str, Any]) -> Dict[str, Any]:
        """Run CVA analysis.
        
        Args:
            landmarks_data: List of landmark arrays
            params: CVA parameters
            
        Returns:
            CVA results dictionary
        """
        self.logger.info(f"Running CVA analysis with params: {params}")
        self.logger.info(f"Landmarks data shape: {len(landmarks_data)}x{len(landmarks_data[0]) if landmarks_data else 0}")
        
        try:
            # Get group information
            groups = params.get('groups', [])
            if not groups:
                raise ValueError("Group information is required for CVA")
            
            # Use existing CVA function
            cva_result = MdStatistics.do_cva_analysis(landmarks_data, groups)
            
            return {
                'analysis_type': 'CVA',
                'canonical_variables': cva_result.get('canonical_variables', []),
                'eigenvalues': cva_result.get('eigenvalues', []),
                'group_centroids': cva_result.get('group_centroids', []),
                'classification': cva_result.get('classification', []),
                'accuracy': cva_result.get('accuracy', 0.0)
            }
            
        except Exception as e:
            raise ValueError(f"CVA analysis failed: {str(e)}")
    
    def _run_manova(self, landmarks_data: List[List], params: Dict[str, Any]) -> Dict[str, Any]:
        """Run MANOVA analysis.
        
        Args:
            landmarks_data: List of landmark arrays
            params: MANOVA parameters
            
        Returns:
            MANOVA results dictionary
        """
        self.logger.debug("Running MANOVA analysis")
        
        try:
            # Get group information
            groups = params.get('groups', [])
            if not groups:
                raise ValueError("Group information is required for MANOVA")
            
            # Use existing MANOVA function
            manova_result = MdStatistics.do_manova_analysis(landmarks_data, groups)
            
            # Format results to match original structure
            stat_dict = {}
            column_names = ["", "Value", "Num DF", "Den DF", "F Value", "Pr > F"]
            
            # Convert test_statistics to the format expected by UI
            if 'test_statistics' in manova_result:
                for stat in manova_result['test_statistics']:
                    stat_name = stat['name']
                    stat_values = [
                        stat['value'],
                        stat['df_num'], 
                        stat['df_den'],
                        stat['f_statistic'],
                        stat['p_value']
                    ]
                    stat_dict[stat_name] = stat_values
            
            stat_dict['column_names'] = column_names
            
            return {
                'analysis_type': 'MANOVA',
                'stat_dict': stat_dict,
                'group_means': manova_result.get('group_means', []),
                'overall_mean': manova_result.get('overall_mean', []),
                'n_groups': manova_result.get('n_groups', 0),
                'group_sizes': manova_result.get('group_sizes', [])
            }
            
        except Exception as e:
            raise ValueError(f"MANOVA analysis failed: {str(e)}")
    
    def _run_procrustes(self, landmarks_data: List[List], params: Dict[str, Any]) -> Dict[str, Any]:
        """Run Procrustes analysis.
        
        Args:
            landmarks_data: List of landmark arrays
            params: Procrustes parameters
            
        Returns:
            Procrustes results dictionary
        """
        self.logger.debug("Running Procrustes analysis")
        
        try:
            # Use existing Procrustes function
            proc_result = MdStatistics.do_procrustes_analysis(
                landmarks_data,
                scaling=params.get('scaling', True),
                reflection=params.get('reflection', True)
            )
            
            return {
                'analysis_type': 'Procrustes',
                'aligned_shapes': proc_result.get('aligned_shapes', []),
                'mean_shape': proc_result.get('mean_shape', []),
                'centroid_sizes': proc_result.get('centroid_sizes', []),
                'consensus_configuration': proc_result.get('consensus', [])
            }
            
        except Exception as e:
            raise ValueError(f"Procrustes analysis failed: {str(e)}")
    
    def delete_analysis(self, analysis_id: int) -> bool:
        """Delete analysis result.
        
        Args:
            analysis_id: ID of analysis to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            analysis = MdModel.MdAnalysis.get_by_id(analysis_id)
            analysis_type = analysis.analysis_type
            
            analysis.delete_instance()
            
            # Clear current selection if it was the deleted analysis
            if self.current_analysis and self.current_analysis.id == analysis_id:
                self.current_analysis = None
            
            self.info_message.emit(f"{analysis_type} analysis deleted")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete analysis {analysis_id}: {e}")
            self.error_occurred.emit(f"Failed to delete analysis: {str(e)}")
            return False
    
    # ========== Export Operations ==========
    
    def export_dataset(self, file_path: str, format: str = 'CSV', 
                      include_metadata: bool = True) -> bool:
        """Export dataset to file.
        
        Args:
            file_path: Output file path
            format: Export format (CSV, Excel, etc.)
            include_metadata: Include dataset metadata
            
        Returns:
            True if successful, False otherwise
        """
        if not self.current_dataset:
            self.error_occurred.emit("No dataset selected for export")
            return False
        
        try:
            self.logger.info(f"Exporting dataset to: {file_path}")
            
            if format.upper() == 'CSV':
                success = mu.export_dataset_to_csv(
                    self.current_dataset, 
                    file_path, 
                    include_metadata
                )
            elif format.upper() == 'EXCEL':
                success = mu.export_dataset_to_excel(
                    self.current_dataset, 
                    file_path, 
                    include_metadata
                )
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            if success:
                self.info_message.emit(f"Dataset exported to {Path(file_path).name}")
                return True
            else:
                raise ValueError("Export function returned False")
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            self.error_occurred.emit(f"Export failed: {str(e)}")
            return False
    
    # ========== State Management ==========
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current application state.
        
        Returns:
            Dictionary containing current state
        """
        return {
            'current_dataset_id': self.current_dataset.id if self.current_dataset else None,
            'current_object_id': self.current_object.id if self.current_object else None,
            'current_analysis_id': self.current_analysis.id if self.current_analysis else None,
            'processing': self._processing
        }
    
    def restore_state(self, state: Dict[str, Any]):
        """Restore application state.
        
        Args:
            state: State dictionary to restore
        """
        try:
            # Restore dataset selection
            dataset_id = state.get('current_dataset_id')
            if dataset_id:
                try:
                    self.current_dataset = MdModel.MdDataset.get_by_id(dataset_id)
                except MdModel.MdDataset.DoesNotExist:
                    self.logger.warning(f"Dataset {dataset_id} not found")
            
            # Restore object selection
            object_id = state.get('current_object_id')
            if object_id:
                try:
                    self.current_object = MdModel.MdObject.get_by_id(object_id)
                except MdModel.MdObject.DoesNotExist:
                    self.logger.warning(f"Object {object_id} not found")
            
            # Restore analysis selection
            analysis_id = state.get('current_analysis_id')
            if analysis_id:
                try:
                    self.current_analysis = MdModel.MdAnalysis.get_by_id(analysis_id)
                except MdModel.MdAnalysis.DoesNotExist:
                    self.logger.warning(f"Analysis {analysis_id} not found")
            
            self.logger.debug("Application state restored")
            
        except Exception as e:
            self.logger.error(f"Failed to restore state: {e}")
    
    # ========== Utility Methods ==========
    
    def get_dataset_summary(self, dataset: MdModel.MdDataset) -> Dict[str, Any]:
        """Get dataset summary information.
        
        Args:
            dataset: Dataset to summarize
            
        Returns:
            Summary dictionary
        """
        try:
            objects = list(dataset.object_list)
            # Handle analysis backref properly
            if hasattr(dataset, 'analysis_set'):
                analyses = list(dataset.analysis_set)
            elif hasattr(dataset, 'analyses'):
                analyses = list(dataset.analyses)
            else:
                analyses = []
            
            return {
                'name': dataset.dataset_name,
                'description': dataset.dataset_desc,
                'dimension': dataset.dimension,
                'landmark_count': dataset.landmark_count,
                'object_count': len(objects),
                'analysis_count': len(analyses),
                'created_at': dataset.created_at,
                'modified_at': dataset.modified_at,
                'has_images': any(hasattr(obj, 'image') and obj.image for obj in objects),
                'has_3d_models': any(hasattr(obj, 'threed_model') and obj.threed_model for obj in objects),
                'has_landmarks': any(obj.landmark_str for obj in objects)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get dataset summary: {e}")
            return {}
    
    def validate_dataset_for_analysis(self, dataset_or_analysis_type):
        """Validate that dataset is suitable for analysis.
        
        Args:
            dataset_or_analysis_type: Either a MdDataset object or analysis type string
            
        Returns:
            bool: True if dataset is valid for analysis, False otherwise
        """
        # Handle different parameter types for backward compatibility
        if isinstance(dataset_or_analysis_type, str):
            # Called with analysis_type string - use current_dataset
            return self._validate_dataset_for_analysis_type(dataset_or_analysis_type)
        else:
            # Called with dataset object - validate for general analysis
            return self._validate_dataset_for_general_analysis(dataset_or_analysis_type)
    
    def _validate_dataset_for_analysis_type(self, analysis_type: str) -> Tuple[bool, str]:
        """Validate that current dataset is suitable for specific analysis type.
        
        Args:
            analysis_type: Type of analysis to validate for
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.current_dataset:
            return False, "No dataset selected"
        
        objects_with_landmarks = list(self.current_dataset.object_list.where(
            (MdModel.MdObject.landmark_str.is_null(False)) & 
            (MdModel.MdObject.landmark_str != "")
        ))
        
        min_objects = {
            'PCA': 2,
            'CVA': 6,  # At least 2 per group, minimum 3 groups
            'MANOVA': 6,
            'PROCRUSTES': 2
        }
        
        required = min_objects.get(analysis_type.upper(), 2)
        
        if len(objects_with_landmarks) < required:
            return False, f"At least {required} objects with landmarks required for {analysis_type}"
        
        # Check landmark consistency
        if objects_with_landmarks:
            expected_count = self.current_dataset.landmark_count
            for obj in objects_with_landmarks:
                obj.unpack_landmark()
                if len(obj.landmark_list) != expected_count:
                    return False, f"Inconsistent landmark count in object '{obj.object_name}'"
        
        return True, "Dataset is valid for analysis"
    
    def _validate_dataset_for_general_analysis(self, dataset) -> bool:
        """Validate that dataset is suitable for general analysis.
        
        Args:
            dataset: MdDataset object to validate
            
        Returns:
            bool: True if dataset is valid for analysis, False otherwise
        """
        from MdHelpers import show_warning
        
        if dataset is None:
            show_warning(None, "No dataset selected")
            return False
        
        # Check if dataset has objects with landmarks
        objects_with_landmarks = list(dataset.object_list.where(
            (MdModel.MdObject.landmark_str.is_null(False)) & 
            (MdModel.MdObject.landmark_str != "")
        ))
        
        if len(objects_with_landmarks) < 5:
            show_warning(None, f"Dataset '{dataset.dataset_name}' has too few objects with landmarks ({len(objects_with_landmarks)}). At least 5 objects required for analysis.")
            return False
        
        # Check for grouping variables (required for CVA/MANOVA)
        grouping_vars = dataset.get_grouping_variable_index_list()
        has_grouping_vars = len(grouping_vars) > 0 and dataset.propertyname_str
        
        if not has_grouping_vars:
            show_warning(None, f"Dataset '{dataset.dataset_name}' has no grouping variables.\n\nCVA and MANOVA analyses require grouping variables.\nOnly PCA analysis will be available.\n\nTo add grouping variables, import data with grouping information\nor use the object property editor.")
            return False
        
        # Check landmark consistency
        if objects_with_landmarks:
            expected_count = dataset.landmark_count
            for obj in objects_with_landmarks:
                obj.unpack_landmark()
                if len(obj.landmark_list) != expected_count:
                    show_warning(None, f"Inconsistent landmark count in object '{obj.object_name}'. Expected {expected_count}, found {len(obj.landmark_list)}.")
                    return False
        
        return True
    
    def is_processing(self) -> bool:
        """Check if controller is currently processing."""
        return self._processing